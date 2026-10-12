"""FastAPI REST API routes for AI pair programmer."""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Query
from app.models.schemas import (
    HealthResponse, StatsResponse, CodebaseIndex,
    RefactorRequest, RefactorPlan, ApplyRequest, ApplyResult,
    BenchmarkSummary, AuthUser, AuditLogEntry
)
from app.services.indexer import CodebaseIndexer
from app.services.refactor_engine import RefactorEngine
from app.services.evaluator import CodebaseEvaluator
from app.services.audit import audit_service
from app.core.config import settings

router = APIRouter()

# Singletons for services
indexer_service = CodebaseIndexer(root_path=".")
engine_service = RefactorEngine(indexer=indexer_service)
evaluator_service = CodebaseEvaluator()

def get_current_user(authorization: Optional[str] = Header(None)) -> AuthUser:
    """Validate authorization header or return demo user if demo mode enabled."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        if token == "invalid" or len(token) < 5:
            raise HTTPException(status_code=401, detail="Invalid token")
        return AuthUser(
            user_id="usr-oidc-verified",
            username="analyst_user",
            email="analyst@alan-vo.local",
            roles=["analyst", "operator"],
            is_authenticated=True
        )

    if settings.auth_demo_mode:
        return AuthUser(
            user_id="usr-demo-local",
            username="local_pair_programmer",
            email=settings.author_email,
            roles=["admin", "analyst", "viewer"],
            is_authenticated=True
        )

    raise HTTPException(status_code=401, detail="Authentication required: Provide Keycloak Bearer token")

@router.get("/health", response_model=HealthResponse)
def get_health():
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        app_name=settings.app_name,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@router.get("/stats", response_model=StatsResponse)
def get_stats():
    index = indexer_service._cached_index or indexer_service.scan(max_files=10)
    return StatsResponse(
        version=settings.app_version,
        author=f"{settings.author_name} <{settings.author_email}>",
        indexed_files_cache=index.total_files,
        plans_generated_total=len(engine_service._plans_cache),
        benchmark_baseline_score=1.0,
        offline_engine_available=True,
        supported_providers=["openai-compatible", "anthropic", "gemini", "ollama"]
    )

@router.get("/index", response_model=CodebaseIndex)
def scan_codebase(
    path: str = Query(".", description="Directory path to scan"),
    max_files: int = Query(25, ge=1, le=100),
    user: AuthUser = Depends(get_current_user)
):
    idx = CodebaseIndexer(root_path=path)
    result = idx.scan(max_files=max_files)
    audit_service.log(
        action="SCAN_CODEBASE",
        user=user.username,
        details={"scanned_files": result.total_files, "symbols": result.symbols_count}
    )
    return result

@router.post("/plan", response_model=RefactorPlan)
def create_plan(
    request: RefactorRequest,
    user: AuthUser = Depends(get_current_user)
):
    if not request.task.strip():
        raise HTTPException(status_code=400, detail="Task description cannot be empty")
    
    plan = engine_service.plan_refactor(request)
    audit_service.log(
        action="GENERATE_REFACTOR_PLAN",
        user=user.username,
        details={"task": request.task, "plan_id": plan.plan_id, "steps_count": len(plan.steps)}
    )
    return plan

@router.get("/plan/{plan_id}", response_model=RefactorPlan)
def get_plan(plan_id: str, user: AuthUser = Depends(get_current_user)):
    plan = engine_service._plans_cache.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Refactor plan not found")
    return plan

@router.post("/apply", response_model=ApplyResult)
def apply_plan(
    request: ApplyRequest,
    user: AuthUser = Depends(get_current_user)
):
    if "admin" not in user.roles and "operator" not in user.roles:
        raise HTTPException(status_code=403, detail="Role 'operator' or 'admin' required to apply patches")

    result = engine_service.apply_plan(plan_id=request.plan_id, confirm=request.confirm)
    audit_service.log(
        action="APPLY_REFACTOR_PLAN",
        user=user.username,
        details={"plan_id": request.plan_id, "confirmed": request.confirm, "success": result.success}
    )
    return result

@router.post("/evaluate", response_model=BenchmarkSummary)
def evaluate_benchmark(user: AuthUser = Depends(get_current_user)):
    summary = evaluator_service.run_benchmark()
    audit_service.log(
        action="RUN_BENCHMARK_EVALUATION",
        user=user.username,
        details={"average_score": summary.average_score, "tasks_count": summary.total_tasks}
    )
    return summary

@router.get("/benchmark", response_model=BenchmarkSummary)
def get_benchmark():
    return evaluator_service.run_benchmark()

@router.get("/audit", response_model=List[AuditLogEntry])
def get_audit_trail(limit: int = Query(50, ge=1, le=200), user: AuthUser = Depends(get_current_user)):
    return audit_service.list_entries(limit=limit)

@router.get("/auth/me", response_model=AuthUser)
def get_current_user_profile(user: AuthUser = Depends(get_current_user)):
    return user
