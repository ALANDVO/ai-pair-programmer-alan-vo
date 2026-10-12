#!/usr/bin/env python3
"""ai-pair-programmer CLI entrypoint."""
import sys
import os

# Add backend directory to sys.path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.cli import run_cli
from app.main import app

def main():
    if len(sys.argv) > 1 and sys.argv[1] not in ("--help", "-h") and not sys.argv[1].startswith("--"):
        run_cli(sys.argv[1:])
    else:
        run_cli(sys.argv[1:])

if __name__ == "__main__":
    main()
