"""Data models and schemas for AI pair programming service."""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class SymbolInfo(BaseModel):
    name: str
    kind: str  # function, class, async_function, method, interface
    line_number: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)

class FileContext(BaseModel):
    path: str
    relative_path: str
    language: str
    size_bytes: int
    lines_count: int
    imports: List[str] = Field(default_factory=list)
    symbols: List[SymbolInfo] = Field(default_factory=list)
    callers: List[str] = Field(default_factory=list)

class DependencyEdge(BaseModel):
    source_file: str
    target_module: str
    imported_names: List[str] = Field(default_factory=list)

class CodebaseIndex(BaseModel):
    root_path: str
    total_files: int
    scanned_extensions: List[str] = Field(default_factory=list)
    files: List[FileContext] = Field(default_factory=list)
    dependencies: List[DependencyEdge] = Field(default_factory=list)
    symbols_count: int = 0

class RefactorStep(BaseModel):
    step_id: int
    file_path: str
    action: str  # "modify", "create", "delete"
    detail: str
    reason: str
    unified_diff: str = ""
    side_effects: List[str] = Field(default_factory=list)
    ast_valid: bool = True
    llm_advisory: Optional[str] = None

class RefactorPlan(BaseModel):
    plan_id: str
    task: str
    summary: str
    steps: List[RefactorStep] = Field(default_factory=list)
    estimated_impact: str = "low"
    potential_risks: List[str] = Field(default_factory=list)
    ast_valid: bool = True
    model_used: str = "deterministic-offline-engine"
    generated_at: str
    llm_advisory: Optional[str] = None
    llm_provider: Optional[str] = None

class RefactorRequest(BaseModel):
    task: str
    path: str = "."
    strategy: str = "conservative"  # conservative, proactive, refactor
    max_files: int = 15
    dry_run: bool = True
    use_llm: bool = False

class DiffHunk(BaseModel):
    old_start: int
    old_length: int
    new_start: int
    new_length: int
    lines: List[str]

class FileDiff(BaseModel):
    file_path: str
    action: str
    hunks: List[DiffHunk] = Field(default_factory=list)
    raw_diff: str

class ApplyRequest(BaseModel):
    plan_id: str
    confirm: bool = False

class ApplyResult(BaseModel):
    success: bool
    plan_id: str
    applied_files: List[str] = Field(default_factory=list)
    message: str
    audit_id: str

class EvaluationTask(BaseModel):
    task_id: str
    name: str
    description: str
    target_file: str
    expected_change_type: str
    code_snippet: str

class EvaluationResult(BaseModel):
    task_id: str
    name: str
    syntactically_valid: bool
    ast_parse_success: bool
    dependency_impact_detected: bool
    diff_generated: bool
    execution_time_ms: float
    score: float

class BenchmarkSummary(BaseModel):
    total_tasks: int
    passed_tasks: int
    valid_syntax_rate: float
    ast_parse_rate: float
    dependency_recall_rate: float
    average_score: float
    engine: str
    results: List[EvaluationResult] = Field(default_factory=list)

class AuthUser(BaseModel):
    user_id: str
    username: str
    email: str
    roles: List[str]
    is_authenticated: bool = True

class AuditLogEntry(BaseModel):
    audit_id: str
    timestamp: str
    action: str
    user: str
    details: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    app_name: str
    timestamp: str

class StatsResponse(BaseModel):
    version: str
    author: str
    indexed_files_cache: int
    plans_generated_total: int
    benchmark_baseline_score: float
    offline_engine_available: bool
    supported_providers: List[str]
