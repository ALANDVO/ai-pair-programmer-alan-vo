"""Unit tests for AST codebase indexer."""
import os
import tempfile
import pytest
from app.services.indexer import CodebaseIndexer

def test_indexer_initialization():
    indexer = CodebaseIndexer(root_path=".")
    assert indexer.root_path is not None

def test_indexer_scan_python_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_file = os.path.join(tmpdir, "sample.py")
        with open(sample_file, "w") as f:
            f.write(
                "import os\n"
                "from sys import path\n\n"
                "class DataProcessor:\n"
                "    \"\"\"Process records.\"\"\"\n"
                "    def process(self, x):\n"
                "        return x * 2\n\n"
                "def helper_func():\n"
                "    return True\n\n"
                "async def async_worker():\n"
                "    return 42\n"
            )

        indexer = CodebaseIndexer(root_path=tmpdir)
        index = indexer.scan(max_files=10)

        assert index.total_files == 1
        fc = index.files[0]
        assert fc.relative_path == "sample.py"
        assert fc.language == "python"
        assert len(fc.imports) >= 2

        sym_names = [s.name for s in fc.symbols]
        assert "DataProcessor" in sym_names
        assert "DataProcessor.process" in sym_names
        assert "helper_func" in sym_names
        assert "async_worker" in sym_names

def test_indexer_caller_resolution():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod_a = os.path.join(tmpdir, "module_a.py")
        mod_b = os.path.join(tmpdir, "module_b.py")
        with open(mod_a, "w") as f:
            f.write("def shared_utility():\n    return 'util'\n")
        with open(mod_b, "w") as f:
            f.write("from module_a import shared_utility\n\ndef run():\n    return shared_utility()\n")

        indexer = CodebaseIndexer(root_path=tmpdir)
        index = indexer.scan(max_files=10)
        file_a = next(x for x in index.files if x.relative_path == "module_a.py")
        assert "module_b.py" in file_a.callers

def test_indexer_handles_syntax_error_gracefully():
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_file = os.path.join(tmpdir, "invalid.py")
        with open(bad_file, "w") as f:
            f.write("def broken(:\n    syntax error here\n")

        indexer = CodebaseIndexer(root_path=tmpdir)
        index = indexer.scan(max_files=5)
        assert index.total_files == 1
        assert index.files[0].relative_path == "invalid.py"

def test_indexer_ignores_hidden_directories():
    with tempfile.TemporaryDirectory() as tmpdir:
        git_dir = os.path.join(tmpdir, ".git")
        os.makedirs(git_dir)
        with open(os.path.join(git_dir, "config.py"), "w") as f:
            f.write("x = 1\n")
        with open(os.path.join(tmpdir, "main.py"), "w") as f:
            f.write("y = 2\n")

        indexer = CodebaseIndexer(root_path=tmpdir)
        index = indexer.scan(max_files=10)
        rel_paths = [f.relative_path for f in index.files]
        assert "main.py" in rel_paths
        assert not any(".git" in p for p in rel_paths)
