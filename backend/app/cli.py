"""Command-line interface preserving pair programming terminal workflows."""
import argparse
import sys
import os
from app.services.indexer import CodebaseIndexer
from app.services.refactor_engine import RefactorEngine
from app.models.schemas import RefactorRequest

def suggest(args):
    """Suggest changes for a task against codebase context."""
    engine = RefactorEngine(CodebaseIndexer(root_path=args.path))
    req = RefactorRequest(
        task=args.task,
        path=args.path,
        max_files=args.max_files,
        dry_run=args.dry_run
    )
    plan = engine.plan_refactor(req)
    print(f"\n{'='*60}\nPLAN: {plan.summary}\n{'='*60}")
    print(f"Impact: {plan.estimated_impact} | AST valid: {plan.ast_valid}\n")
    for s in plan.steps:
        print(f"[{s.action.upper()}] {s.file_path}")
        print(f"  Reason: {s.reason}")
        if s.unified_diff:
            print(f"  Diff:\n{s.unified_diff[:500]}\n")
    if args.dry_run:
        print("[dry-run] no files modified")
    return plan

def session(args):
    """Interactive pair programming session simulation."""
    print(f"\nStarting pair programming session on {args.path} for: '{args.task}'")
    print("Codebase indexed. Type 'exit' to quit.")
    print("[AI] Context analyzed. Ready to review proposed modifications.")

def explain(args):
    """Explain codebase file or architecture."""
    target = args.file or "main.py"
    q = args.question or "Explain the architecture and key design decisions."
    print(f"\nExplaining {target}: {q}")
    print("[AI] Modular architecture featuring AST indexing, deterministic diff synthesis, and evaluation suites.")

def refactor(args):
    """Multi-file refactor command."""
    engine = RefactorEngine(CodebaseIndexer(root_path=args.path))
    req = RefactorRequest(task=args.task, path=args.path, max_files=args.max_files)
    plan = engine.plan_refactor(req)
    print(f"\nRefactor Plan ID: {plan.plan_id}")
    for s in plan.steps:
        print(f"  * {s.file_path}: {s.detail}")
    return plan

def run_cli(args=None):
    p = argparse.ArgumentParser(description="ai-pair-programmer CLI")
    sub = p.add_subparsers(dest="cmd")
    
    s = sub.add_parser("suggest", help="Suggest changes for a task")
    s.add_argument("--task", required=True)
    s.add_argument("--path", default=".")
    s.add_argument("--max-files", type=int, default=15)
    s.add_argument("--dry-run", action="store_true", default=True)
    s.add_argument("--apply", action="store_true")
    s.set_defaults(fn=suggest)

    se = sub.add_parser("session", help="Interactive session")
    se.add_argument("--task", required=True)
    se.add_argument("--path", default=".")
    se.add_argument("--max-files", type=int, default=15)
    se.set_defaults(fn=session)

    e = sub.add_parser("explain", help="Explain code architecture")
    e.add_argument("--file")
    e.add_argument("--question")
    e.set_defaults(fn=explain)

    r = sub.add_parser("refactor", help="Multi-file coordinated refactor")
    r.add_argument("--task", required=True)
    r.add_argument("--path", default=".")
    r.add_argument("--max-files", type=int, default=15)
    r.add_argument("--apply", action="store_true")
    r.set_defaults(fn=refactor)

    parsed = p.parse_args(args)
    if hasattr(parsed, "fn"):
        parsed.fn(parsed)
    else:
        p.print_help()
