/**
 * TypeScript definitions for AI Pair Programmer
 */

export interface SymbolInfo {
  name: string;
  kind: string;
  line_number: number;
  signature?: string;
  docstring?: string;
  dependencies: string[];
}

export interface FileContext {
  path: string;
  relative_path: string;
  language: string;
  size_bytes: number;
  lines_count: number;
  imports: string[];
  symbols: SymbolInfo[];
  callers: string[];
}

export interface DependencyEdge {
  source_file: string;
  target_module: string;
  imported_names: string[];
}

export interface CodebaseIndex {
  root_path: string;
  total_files: number;
  scanned_extensions: string[];
  files: FileContext[];
  dependencies: DependencyEdge[];
  symbols_count: number;
}

export interface RefactorStep {
  step_id: number;
  file_path: string;
  action: string;
  detail: string;
  reason: string;
  unified_diff: string;
  side_effects: string[];
  ast_valid: boolean;
}

export interface RefactorPlan {
  plan_id: string;
  task: string;
  summary: string;
  steps: RefactorStep[];
  estimated_impact: string;
  potential_risks: string[];
  ast_valid: boolean;
  model_used: string;
  generated_at: string;
}

export interface RefactorRequest {
  task: string;
  path?: string;
  strategy?: string;
  max_files?: number;
  dry_run?: boolean;
  use_llm?: boolean;
}

export interface ApplyRequest {
  plan_id: string;
  confirm: boolean;
}

export interface ApplyResult {
  success: boolean;
  plan_id: string;
  applied_files: string[];
  message: string;
  audit_id: string;
}

export interface EvaluationResult {
  task_id: string;
  name: string;
  syntactically_valid: boolean;
  ast_parse_success: boolean;
  dependency_impact_detected: boolean;
  diff_generated: boolean;
  execution_time_ms: number;
  score: number;
}

export interface BenchmarkSummary {
  total_tasks: number;
  passed_tasks: number;
  valid_syntax_rate: number;
  ast_parse_rate: number;
  dependency_recall_rate: number;
  average_score: number;
  engine: string;
  results: EvaluationResult[];
}

export interface AuthUser {
  user_id: string;
  username: string;
  email: string;
  roles: string[];
  is_authenticated: boolean;
}

export interface StatsResponse {
  version: string;
  author: string;
  indexed_files_cache: number;
  plans_generated_total: number;
  benchmark_baseline_score: number;
  offline_engine_available: boolean;
  supported_providers: string[];
}
