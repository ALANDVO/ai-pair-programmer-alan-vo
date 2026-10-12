"""Unit tests for AI/ML evaluation benchmark suite."""
import pytest
from app.services.evaluator import CodebaseEvaluator

def test_evaluator_runs_benchmarks():
    evaluator = CodebaseEvaluator()
    summary = evaluator.run_benchmark()

    assert summary.total_tasks >= 5
    assert summary.passed_tasks >= 4
    assert summary.valid_syntax_rate >= 0.8
    assert summary.ast_parse_rate >= 0.8
    assert summary.dependency_recall_rate >= 0.8
    assert summary.average_score >= 0.8
    assert len(summary.results) == summary.total_tasks

def test_benchmark_task_details():
    evaluator = CodebaseEvaluator()
    summary = evaluator.run_benchmark()

    task_0 = summary.results[0]
    assert task_0.task_id == "bench-01"
    assert task_0.syntactically_valid is True
    assert task_0.ast_parse_success is True
    assert task_0.execution_time_ms >= 0.0
