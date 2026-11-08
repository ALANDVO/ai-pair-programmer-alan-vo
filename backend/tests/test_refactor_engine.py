"""Unit tests for deterministic refactor engine and unified diff synthesis."""
import os
import tempfile
import pytest
from app.services.indexer import CodebaseIndexer
from app.services.refactor_engine import RefactorEngine
from app.models.schemas import RefactorRequest

def test_plan_rename_refactor():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "service.py")
        with open(src, "w") as f:
            f.write("def calculate_tax(amount):\n    return amount * 0.1\n")

        engine = RefactorEngine(CodebaseIndexer(root_path=tmpdir))
        req = RefactorRequest(task="rename calculate_tax to compute_tax", path=tmpdir)
        plan = engine.plan_refactor(req)

        assert plan.plan_id.startswith("plan-")
        assert len(plan.steps) == 1
        assert plan.steps[0].action == "modify"
        assert "compute_tax" in plan.steps[0].unified_diff
        assert plan.steps[0].ast_valid is True

def test_plan_retry_wrapper_injection():
    with tempfile.TemporaryDirectory() as tmpdir:
        client_file = os.path.join(tmpdir, "api_client.py")
        with open(client_file, "w") as f:
            f.write("def fetch_data():\n    return 'data'\n")

        engine = RefactorEngine(CodebaseIndexer(root_path=tmpdir))
        req = RefactorRequest(task="add retry wrapper with exponential backoff", path=tmpdir)
        plan = engine.plan_refactor(req)

        assert len(plan.steps) >= 1
        assert any("with_exponential_backoff" in step.detail for step in plan.steps)
        assert plan.steps[0].ast_valid is True

def test_plan_audit_logging_injection():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "db.py")
        with open(db_file, "w") as f:
            f.write("def update_record(id, data):\n    pass\n")

        engine = RefactorEngine(CodebaseIndexer(root_path=tmpdir))
        req = RefactorRequest(task="add audit logging for state mutation", path=tmpdir)
        plan = engine.plan_refactor(req)

        assert len(plan.steps) >= 1
        assert "log_audit_event" in plan.steps[0].unified_diff
        assert plan.steps[0].ast_valid is True

def test_unified_diff_format():
    engine = RefactorEngine()
    orig = "line 1\nline 2\nline 3\n"
    mod = "line 1\nline 2 modified\nline 3\n"
    diff = engine._create_unified_diff(orig, mod, "test.txt")
    assert "--- a/test.txt" in diff
    assert "+++ b/test.txt" in diff
    assert "+line 2 modified" in diff

def test_ast_verification():
    engine = RefactorEngine()
    assert engine._verify_ast("x = 1\ny = 2\n", "python") is True
    assert engine._verify_ast("def syntax_error(:", "python") is False
    assert engine._verify_ast("const x = 1;", "typescript") is True

def test_apply_plan_dry_run_and_confirm():
    """Test dry-run and confirm modes (confirm currently stubbed - doesn't modify files)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fpath = os.path.join(tmpdir, "app.py")
        with open(fpath, "w") as f:
            f.write("def hello():\n    return 'world'\n")

        engine = RefactorEngine(CodebaseIndexer(root_path=tmpdir))
        req = RefactorRequest(task="rename hello to greet", path=tmpdir)
        plan = engine.plan_refactor(req)

        dry_run = engine.apply_plan(plan.plan_id, confirm=False)
        assert dry_run.success is True
        assert "dry-run" in dry_run.message
        assert dry_run.applied_files == ["app.py"]

        # Note: confirm=True currently doesn't actually apply diffs (stubbed)
        confirm_result = engine.apply_plan(plan.plan_id, confirm=True)
        assert confirm_result.success is True
        assert "Applied changes" in confirm_result.message

def test_plan_with_llm_advisory_fallback_when_unconfigured():
    """Test that use_llm=True falls back to deterministic mode when no API key is configured."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "service.py")
        with open(src, "w") as f:
            f.write("def calculate_tax(amount):\n    return amount * 0.1\n")

        engine = RefactorEngine(CodebaseIndexer(root_path=tmpdir))
        req = RefactorRequest(task="rename calculate_tax to compute_tax", path=tmpdir, use_llm=True)
        plan = engine.plan_refactor(req)

        assert plan.plan_id.startswith("plan-")
        assert len(plan.steps) == 1
        assert plan.model_used == "deterministic-offline-engine"
        assert plan.llm_advisory is not None
        assert "deterministic" in plan.llm_advisory.lower()
        assert plan.llm_provider == "offline"
        # Steps should have LLM advisory from deterministic fallback
        assert plan.steps[0].llm_advisory is not None
        assert "deterministic" in plan.steps[0].llm_advisory.lower()

def test_plan_with_llm_advisory_flag_in_request():
    """Test that use_llm flag is properly passed and reflected in plan."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "service.py")
        with open(src, "w") as f:
            f.write("def fetch_data():\n    return 'data'\n")

        engine = RefactorEngine(CodebaseIndexer(root_path=tmpdir))
        req_false = RefactorRequest(task="add retry wrapper", path=tmpdir, use_llm=False)
        req_true = RefactorRequest(task="add retry wrapper", path=tmpdir, use_llm=True)

        plan_false = engine.plan_refactor(req_false)
        plan_true = engine.plan_refactor(req_true)

        # Both should succeed
        assert plan_false.plan_id != plan_true.plan_id
        assert plan_false.llm_advisory is None
        assert plan_true.llm_advisory is not None  # Deterministic fallback when unconfigured
        assert plan_false.model_used == "deterministic-offline-engine"
        assert plan_true.model_used == "deterministic-offline-engine"
