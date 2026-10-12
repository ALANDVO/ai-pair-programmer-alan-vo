"""Integration tests for FastAPI REST API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"

def test_stats_endpoint():
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.0.0"
    assert "Alan Vo" in data["author"]
    assert data["offline_engine_available"] is True

def test_codebase_index_endpoint():
    resp = client.get("/api/index?path=.&max_files=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_files"] >= 1
    assert "files" in data

def test_plan_generation_and_retrieval_workflow():
    payload = {
        "task": "rename calculate_tax to compute_tax",
        "path": ".",
        "max_files": 10,
        "dry_run": True
    }
    resp = client.post("/api/plan", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "plan_id" in data
    plan_id = data["plan_id"]
    assert data["ast_valid"] is True

    # Retrieve by plan_id
    get_resp = client.get(f"/api/plan/{plan_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["plan_id"] == plan_id

def test_plan_validation_empty_task():
    payload = {"task": "   ", "path": "."}
    resp = client.post("/api/plan", json=payload)
    assert resp.status_code == 400

def test_apply_endpoint_dry_run():
    # First create plan
    plan_resp = client.post("/api/plan", json={"task": "add retry wrapper", "path": "."})
    plan_id = plan_resp.json()["plan_id"]

    resp = client.post("/api/apply", json={"plan_id": plan_id, "confirm": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "[dry-run]" in data["message"]

def test_benchmark_endpoint():
    resp = client.post("/api/evaluate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tasks"] >= 5
    assert data["average_score"] >= 0.8

def test_audit_endpoint():
    resp = client.get("/api/audit")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_unauthenticated_rejection_when_demo_disabled():
    orig_demo = settings.auth_demo_mode
    try:
        settings.auth_demo_mode = False
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401
    finally:
        settings.auth_demo_mode = orig_demo

def test_bearer_token_authentication():
    headers = {"Authorization": "Bearer valid-test-token-value"}
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "analyst_user"
