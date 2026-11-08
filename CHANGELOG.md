# Changelog

## 1.4.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.2.1] - 2026-11-05

### Added
- **Context-Aware LLM Advisory**: Refactoring type (rename, retry wrapper, audit logging, generic) now passed to LLM adapter for more targeted advisory explanations.
- **Enhanced Deterministic Fallback**: Offline fallback explanations now include refactoring type context for better clarity.
- **Improved LLM Prompts**: System prompt augmented with refactoring type to guide more specific implementation reasoning.

### Changed
- Updated `LLMAdapter.generate_explanation()` signature to accept optional `refactor_type` parameter.
- Updated `RefactorEngine.plan_refactor()` to detect and pass refactoring type to LLM advisory calls.

Author: Alan Vo <alanvo@gmail.com>

## [1.2.2] - 2026-11-08

### Added
- **Deterministic Fallback Advisory on Demand**: When `use_llm=true` but no LLM API key is configured, the system now returns the deterministic offline advisory explanation instead of silently skipping it. This ensures users who opt-in to LLM advisory always receive reasoning, with clear labeling of the source (offline engine vs. LLM provider).
- **Updated Test Coverage**: Tests updated to verify deterministic advisory is provided when `use_llm=true` without API configuration.

### Changed
- Modified `RefactorEngine.plan_refactor()` to call LLM adapter whenever `request.use_llm` is true, allowing the adapter's built-in fallback to provide deterministic explanations.
- Updated `test_plan_with_llm_advisory_fallback_when_unconfigured` and `test_plan_with_llm_advisory_flag_in_request` to reflect new expected behavior.

Author: Alan Vo <alanvo@gmail.com>

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-10-12

### Added
- **Core AST Codebase Indexer**: Static code analysis extracting class hierarchies, function signatures, import statements, and cross-file call graphs.
- **Deterministic Refactor Planner**: Rule-based and AST-guided multi-file edit synthesis with dependency impact analysis, side-effect detection, and unified diff generation.
- **Offline Deterministic Fallback**: Safe fallback engine that generates syntactic refactorings without requiring external LLM API credentials.
- **Provider-Agnostic LLM Adapter**: Extensible adapter supporting OpenAI-compatible endpoints, Anthropic messages, Gemini generateContent, and local Ollama with timeout limits and secret redaction.
- **AI/ML Evaluation Suite**: Benchmark runner assessing refactor plan patch validity, AST parse correctness, and dependency side-effect recall against test cases.
- **FastAPI REST API**: Endpoints for codebase indexing, refactoring plans, diff previews, benchmark evaluation, and health/stats metrics.
- **React + TypeScript Dashboard**: Interactive UI with codebase context tree, task configuration, unified diff inspector, and evaluation metrics viewer.
- **Containerization & CI**: Dockerfiles for backend and frontend with non-root security profiles, compose orchestration with Keycloak broker, and GitHub Actions CI workflow.

## [1.0.1] - 2026-10-20

### Added
- **LLM Advisory Integration**: Refactor engine now calls LLM adapter when `use_llm=true` in request, incorporating advisory reasoning into plan summary and individual steps.
- **Frontend LLM Toggle**: TaskForm component exposes "Use LLM Advisory Reasoning" checkbox to opt-in to LLM-powered explanations.
- **Deterministic Fallback Preserved**: When no LLM API key is configured, system gracefully falls back to deterministic offline engine with clear labeling.
- **Test Coverage**: Added backend tests for LLM advisory fallback behavior and frontend test for TaskForm use_llm checkbox.

Author: Alan Vo <alanvo@gmail.com>

---

Alan Vo · [alanvo.net](https://alanvo.net) · [X: @alanvoasi](https://x.com/alanvoasi)
