# Changelog

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

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
