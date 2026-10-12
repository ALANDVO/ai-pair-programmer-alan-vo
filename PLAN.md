# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

codebase-indexing-and-plan-generation

## Roadmap

### codebase-indexing-and-plan-generation — Codebase AST indexing and deterministic refactoring plan generation

Status: done

Acceptance:
- Indexes codebase files, extracting imports, symbols, and dependency relationships
- Generates multi-file refactoring plans with unified diffs, reasoning, and side-effect predictions
- Provides FastAPI REST endpoints for repository scanning, task planning, and patch preview
- Provides interactive React web UI with task composer, file tree context inspector, and unified diff preview
- Deterministic offline core works without external LLM keys

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/models/schemas.py`, `backend/app/services/indexer.py`, `backend/app/services/refactor_engine.py`, `backend/app/services/evaluator.py`, `backend/app/services/llm_adapter.py`, `backend/app/api/routes.py`, `frontend/src/types/index.ts`, `frontend/src/api/client.ts`, `frontend/src/components/Dashboard.tsx`, `frontend/src/components/DiffViewer.tsx`, `frontend/src/components/TaskForm.tsx`, `frontend/src/App.tsx`, `frontend/src/main.tsx`

Tests: `backend/tests/test_indexer.py`, `backend/tests/test_refactor_engine.py`, `backend/tests/test_evaluator.py`, `backend/tests/test_api.py`, `frontend/src/__tests__/App.test.tsx`, `frontend/src/__tests__/Dashboard.test.tsx`, `frontend/src/__tests__/TaskForm.test.tsx`

### interactive-session-and-undo-history — Interactive session threads and undo rollback stack

Status: planned

Acceptance:
- Multi-turn conversational pair programming sessions with context tracking
- Transactional patch rollback stack with undo logging and state recovery

### oidc-keycloak-auth-and-rbac — OIDC Keycloak authentication and role-based access control

Status: planned

Acceptance:
- Keycloak OIDC PKCE code flow authentication with viewer, analyst, and admin roles
- Enforced authorization on API endpoints and token validation

### multi-model-evaluation-and-benchmark-suite — Automated multi-model benchmark evaluation suite

Status: planned

Acceptance:
- Empirical benchmark runner evaluating patch validity, AST correctness, and side-effect recall across models
- Exportable benchmark metrics and comparative evaluation report

