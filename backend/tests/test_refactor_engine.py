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
            f.write("def calculate_tax(amount):\n    return amount * 0.1\n\ndef invoice():\n    return calculate_tax(100)\n")

        engine = RefactorEngine(CodebaseIndexer(root_path=tmpdir))
        req = RefactorRequest(task="rename calculate_tax to compute_tax", path=tmpdir)
        plan = engine.plan_refactor(req)

        assert plan.plan_id.startswith("plan-")
        assert len(plan.steps) == 1
        step = plan.steps[0]
        assert step.action == "modify"
        assert "compute_tax" in step.unified_diff
        assert step.ast_valid is True

def test_plan_retry_wrapper_injection():
    with tempfile.TemporaryDirectory() as tmpdir:
        client_file = os.path.join(tmpdir, "api_client.py")
        with open(client_file, "w") as f:
            f.write("def fetch_user(uid):\n    return {'id': uid}\n")

        engine = RefactorEngine(CodebaseIndexer(root_path=tmpdir))
        req = RefactorRequest(task="add retry wrapper with backoff", path=tmpdir)
        plan = engine.plan_refactor(req)

        assert len(plan.steps) >= 1
        step = plan.steps[0]
        assert "with_exponential_backoff" in step.detail
        assert step.ast_valid is True

def test_plan_audit_logging_injection():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "db.py")
        with open(db_file, "w") as f:
            f.write("def update_record(id, val):\n    pass\n")

        engine = RefactorEngine(CodebaseIndexer(root_path=tmpdir))
        req = RefactorRequest(task="add audit logging for state mutation", path=tmpdir)
        plan = engine.plan_refactor(req)

        assert len(plan.steps) >= 1
        assert "log_audit_event" in plan.steps[0].unified_diff

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
    with tempfile.TemporaryDirectory() as tmpdir:
        fpath = os.path.join(tmpdir, "app.py")
        with open(fpath, "w") as f:
            f.write("val = 10\n")

        engine = RefactorEngine(CodebaseIndexer(root_path=tmpdir))
        req = RefactorRequest(task="rename val to score", path=tmpdir)
        plan = engine.plan_refactor(req)

        # Dry run
        dry_result = engine.apply_plan(plan.plan_id, confirm=False)
        assert dry_result.success is True
        assert "[dry-run]" in dry_result.message

        # Confirm
        confirm_result = engine.apply_plan(plan.plan_id, confirm=True)
        assert confirm_result.success is True
