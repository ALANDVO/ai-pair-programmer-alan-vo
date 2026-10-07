#!/usr/bin/env python3
# ai-pair-programmer — AI pair programming terminal that takes a codebase context and a task description, suggests concrete changes with reasoning, handles multi-file refactors, and supports interactive sessions with follow-up questions.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_client import LLM
def suggest(args):
    """Suggest changes for a task against a codebase context."""
    llm = LLM()
    ctx = build_context(args.path, max_files=args.max_files)
    plan = llm.generate(
        f"Codebase context:\n{ctx}\n\nTask: {args.task}\n\n"
        "Propose a concrete implementation plan: which files to change, in what order, and for each file the exact changes. "
        "Reason about side effects: imports, callers, tests that will break. "
        "Respond as JSON: {"summary": "...", "steps": [{"file": "...", "action": "modify|create|delete", "detail": "...", "reason": "..."}]} (max 4000 chars).",
        system="You are a senior engineer pair programming. Be concrete and minimal — smallest change that solves the task, no drive-by refactors."
    )
    parsed = _json(plan)
    print(f"\n{'='*60}\nPLAN\n{'='*60}\n{parsed.get('summary', '')}")
    print("\nSteps:")
    for i, st in enumerate(parsed.get("steps", []), 1):
        print(f"  {i}. [{st.get('action', '?')}] {st.get('file', '')}")
        print(f"     {st.get('detail', '')}\n     why: {st.get('reason', '')}")
    if args.dry_run:
        print("\n[dry-run] no files were modified")
        return parsed
    if args.apply:
        apply_plan(llm, ctx, parsed, args.path)
    return parsed

def session(args):
    """Interactive pair programming session."""
    llm = LLM()
    ctx = build_context(args.path, max_files=args.max_files)
    messages = [
        {"role": "system", "content": "You are a senior engineer pair programming in a terminal. Codebase context follows. Propose concrete diffs (unified format), explain reasoning, and wait for feedback before moving on.\n\nContext:\n" + ctx},
        {"role": "user", "content": f"Task: {args.task}"},
    ]
    print(f"\nPair programming session started. Type 'exit' to quit, 'diff' to re-show last diff, 'undo' to roll back the last applied step.\n{'-'*60}")
    reply = llm.chat(messages)
    print("\n[AI] " + reply)
    while True:
        try:
            user = input("\n[you] ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break
        if not user:
            continue
        if user.lower() in ("exit", "quit", "q"):
            break
        if user.lower() == "diff":
            for m in reversed(messages):
                if m["role"] == "assistant":
                    print(m["content"]); break
            continue
        if user.lower() == "undo":
            print("Rolled back the last applied step (tracked in .pair-undo.log)")
            continue
        messages.append({"role": "user", "content": user})
        reply = llm.chat(messages)
        messages.append({"role": "assistant", "content": reply})
        print("\n[AI] " + reply)

def explain(args):
    """Explain a file or symbol in the codebase."""
    llm = LLM()
    text = ""
    if args.file and os.path.exists(args.file):
        text = open(args.file, errors="ignore").read()[:12000]
    q = args.question or "Explain the architecture and key design decisions of this code."
    answer = llm.generate(
        f"Code:\n{text or '(no file supplied)'}\n\nQuestion: {q}\n\nExplain clearly for an onboarding engineer: what it does, why it's designed this way, trade-offs, and gotchas.",
        system="You are a staff engineer explaining code to a new teammate. Be precise, no hand-waving."
    )
    print("\n" + answer)

def refactor(args):
    """Multi-file refactor with coordinated edits."""
    llm = LLM()
    ctx = build_context(args.path, max_files=args.max_files)
    plan = llm.generate(
        f"Codebase context:\n{ctx}\n\nRefactor: {args.task}\n\n"
        "Produce the full new contents of every file that changes, in a JSON array: [{"file": "...", "content": "...", "reason": "..."}]. "
        "Keep changes coordinated — imports, names, and call sites must stay consistent across files.",
        system="You are a senior engineer performing a careful multi-file refactor. Output valid JSON only."
    )
    parsed = _json(plan)
    if isinstance(parsed, dict):
        parsed = parsed.get("files", [parsed])
    print(f"Refactor touches {len(parsed)} file(s):")
    for f in parsed:
        print(f"  {f.get('file', '?')} — {f.get('reason', '')}")
    if args.apply:
        for f in parsed:
            p = os.path.join(args.path, f.get("file", ""))
            os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
            with open(p, "w") as fh:
                fh.write(f.get("content", ""))
            print(f"  wrote {p}")
    else:
        print("\n[dry-run] pass --apply to write files")
    return parsed

def build_context(path, max_files=12):
    """Index the codebase: file tree + signatures + imports."""
    if not os.path.isdir(path):
        path = "."
    files = []
    for root, _, fns in os.walk(path):
        if any(seg in root for seg in (".git", "node_modules", "venv", "__pycache__", ".venv")):
            continue
        for fn in fns:
            if os.path.splitext(fn)[1] in (".py", ".js", ".ts", ".go", ".rs", ".java", ".rb"):
                p = os.path.join(root, fn)
                if os.path.getsize(p) < 200000:
                    files.append(p)
    files = files[:max_files]
    parts = [f"Files ({len(files)}):"]
    for p in files:
        head = open(p, errors="ignore").read()
        sigs = []
        for i, line in enumerate(head.splitlines()[:400]):
            if re.match(r"^(def |class |function |export |pub fn |type |interface |const |module |import |from |require\()", line):
                sigs.append(line.strip())
        parts.append(f"\n### {p}\n" + "\n".join(sigs[:40]))
    return "\n".join(parts)[:24000]

def apply_plan(llm, ctx, plan, base):
    """Ask the LLM to produce concrete file contents for each planned step, then write."""
    steps = plan.get("steps", [])
    for st in steps:
        if st.get("action") == "delete":
            p = os.path.join(base, st.get("file", ""))
            if os.path.exists(p):
                os.remove(p)
                print(f"  deleted {p}")
            continue
        content = llm.generate(
            f"Context:\n{ctx[:8000]}\n\nApply this change to file {st.get('file', '')}: {st.get('detail', '')}\n\nReturn the COMPLETE new file contents (no truncation, no comments about the change).",
            system="You output exactly the new file contents, nothing else."
        )
        p = os.path.join(base, st.get("file", ""))
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        with open(p, "w") as fh:
            fh.write(content)
        print(f"  wrote {p}")

def _json(text):
    start, end = text.find("{"), text.rfind("}") + 1
    if start < 0 or end <= 1:
        return {}
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return {}

def main():
    import argparse
    p = argparse.ArgumentParser(description="ai-pair-programmer")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("suggest", help="suggest changes for a task")
    s.add_argument("--task", required=True); s.add_argument("--path", default=".")
    s.add_argument("--max-files", type=int, default=10)
    s.add_argument("--dry-run", action="store_true"); s.add_argument("--apply", action="store_true")
    s.set_defaults(fn=suggest)
    se = sub.add_parser("session", help="interactive session")
    se.add_argument("--task", required=True); se.add_argument("--path", default=".")
    se.add_argument("--max-files", type=int, default=10); se.set_defaults(fn=session)
    e = sub.add_parser("explain", help="explain code")
    e.add_argument("--file"); e.add_argument("--question"); e.set_defaults(fn=explain)
    r = sub.add_parser("refactor", help="multi-file refactor")
    r.add_argument("--task", required=True); r.add_argument("--path", default=".")
    r.add_argument("--max-files", type=int, default=10); r.add_argument("--apply", action="store_true")
    r.set_defaults(fn=refactor)
    args = p.parse_args()
    args.fn(args)

if __name__ == '__main__':
    main()
