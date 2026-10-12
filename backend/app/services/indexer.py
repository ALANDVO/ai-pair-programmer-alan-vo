"""AST-based codebase context indexer and static dependency graph builder."""
import ast
import os
import re
from typing import List, Dict, Tuple, Optional
from app.models.schemas import CodebaseIndex, FileContext, SymbolInfo, DependencyEdge
from app.core.config import settings

IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", "dist",
    "build", ".pytest_cache", ".mypy_cache", ".ruff_cache", "coverage",
    ".antigravitycli", ".omp", ".idea", ".vscode"
}

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript-react",
    ".js": "javascript",
    ".jsx": "javascript-react",
    ".go": "go",
    ".rs": "rust"
}

class CodebaseIndexer:
    def __init__(self, root_path: str = "."):
        self.root_path = os.path.abspath(root_path)
        self._cached_index: Optional[CodebaseIndex] = None

    def scan(self, max_files: int = 50) -> CodebaseIndex:
        """Scan directory and index files, AST symbols, and dependency edges."""
        files_found: List[str] = []
        for dirpath, dirnames, filenames in os.walk(self.root_path):
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
            for f in sorted(filenames):
                ext = os.path.splitext(f)[1]
                if ext in SUPPORTED_EXTENSIONS:
                    full_p = os.path.join(dirpath, f)
                    try:
                        if os.path.getsize(full_p) <= settings.max_file_size_bytes:
                            files_found.append(full_p)
                    except OSError:
                        continue

        selected_files = files_found[:max_files]
        file_contexts: List[FileContext] = []
        dependency_edges: List[DependencyEdge] = []
        total_symbols = 0

        for path in selected_files:
            ctx, edges = self._analyze_file(path)
            file_contexts.append(ctx)
            dependency_edges.extend(edges)
            total_symbols += len(ctx.symbols)

        # Cross-reference caller references
        self._resolve_callers(file_contexts)

        index = CodebaseIndex(
            root_path=self.root_path,
            total_files=len(file_contexts),
            scanned_extensions=sorted(list(SUPPORTED_EXTENSIONS.keys())),
            files=file_contexts,
            dependencies=dependency_edges,
            symbols_count=total_symbols
        )
        self._cached_index = index
        return index

    def _analyze_file(self, full_path: str) -> Tuple[FileContext, List[DependencyEdge]]:
        rel_path = os.path.relpath(full_path, self.root_path)
        ext = os.path.splitext(full_path)[1]
        lang = SUPPORTED_EXTENSIONS.get(ext, "text")

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            content = ""

        lines = content.splitlines()
        size_bytes = len(content.encode("utf-8"))

        if lang == "python":
            symbols, imports, edges = self._parse_python(rel_path, content)
        else:
            symbols, imports, edges = self._parse_regex_lang(rel_path, content, lang)

        ctx = FileContext(
            path=full_path,
            relative_path=rel_path,
            language=lang,
            size_bytes=size_bytes,
            lines_count=len(lines),
            imports=imports,
            symbols=symbols,
            callers=[]
        )
        return ctx, edges

    def _parse_python(self, rel_path: str, content: str) -> Tuple[List[SymbolInfo], List[str], List[DependencyEdge]]:
        symbols: List[SymbolInfo] = []
        imports: List[str] = []
        edges: List[DependencyEdge] = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fall back to regex parsing if file has syntax error
            return self._parse_regex_lang(rel_path, content, "python")

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
                    edges.append(DependencyEdge(source_file=rel_path, target_module=alias.name, imported_names=[alias.name]))
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                names = [alias.name for alias in node.names]
                imports.append(f"from {mod} import {', '.join(names)}")
                edges.append(DependencyEdge(source_file=rel_path, target_module=mod, imported_names=names))
            elif isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                symbols.append(SymbolInfo(
                    name=node.name,
                    kind="class",
                    line_number=node.lineno,
                    signature=f"class {node.name}",
                    docstring=doc
                ))
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        kind = "async_method" if isinstance(item, ast.AsyncFunctionDef) else "method"
                        symbols.append(SymbolInfo(
                            name=f"{node.name}.{item.name}",
                            kind=kind,
                            line_number=item.lineno,
                            signature=f"def {item.name}(...)",
                            docstring=ast.get_docstring(item)
                        ))
            elif isinstance(node, ast.FunctionDef):
                symbols.append(SymbolInfo(
                    name=node.name,
                    kind="function",
                    line_number=node.lineno,
                    signature=f"def {node.name}(...)",
                    docstring=ast.get_docstring(node)
                ))
            elif isinstance(node, ast.AsyncFunctionDef):
                symbols.append(SymbolInfo(
                    name=node.name,
                    kind="async_function",
                    line_number=node.lineno,
                    signature=f"async def {node.name}(...)",
                    docstring=ast.get_docstring(node)
                ))

        return symbols, imports, edges

    def _parse_regex_lang(self, rel_path: str, content: str, lang: str) -> Tuple[List[SymbolInfo], List[str], List[DependencyEdge]]:
        symbols: List[SymbolInfo] = []
        imports: List[str] = []
        edges: List[DependencyEdge] = []

        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            sline = line.strip()
            # Imports
            if sline.startswith("import ") or sline.startswith("from ") or "require(" in sline:
                imports.append(sline)
                mod_match = re.search(r"['\"]([^'\"]+)['\"]", sline)
                if mod_match:
                    edges.append(DependencyEdge(source_file=rel_path, target_module=mod_match.group(1), imported_names=[]))
            # Definitions
            if re.match(r"^(export\s+)?(class|interface|type)\s+([A-Za-z0-9_]+)", sline):
                m = re.match(r"^(export\s+)?(class|interface|type)\s+([A-Za-z0-9_]+)", sline)
                if m:
                    symbols.append(SymbolInfo(name=m.group(3), kind=m.group(2), line_number=idx, signature=sline))
            elif re.match(r"^(export\s+)?(async\s+)?function\s+([A-Za-z0-9_]+)", sline):
                m = re.match(r"^(export\s+)?(async\s+)?function\s+([A-Za-z0-9_]+)", sline)
                if m:
                    symbols.append(SymbolInfo(name=m.group(3), kind="function", line_number=idx, signature=sline))
            elif re.match(r"^(export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(async\s*)?\(", sline):
                m = re.match(r"^(export\s+)?const\s+([A-Za-z0-9_]+)", sline)
                if m:
                    symbols.append(SymbolInfo(name=m.group(2), kind="arrow_function", line_number=idx, signature=sline))

        return symbols, imports, edges

    def _resolve_callers(self, files: List[FileContext]) -> None:
        """Find other files that reference symbols defined in each file."""
        symbol_map: Dict[str, str] = {}
        for f in files:
            for s in f.symbols:
                symbol_map[s.name] = f.relative_path

        for f in files:
            try:
                with open(f.path, "r", encoding="utf-8", errors="ignore") as fh:
                    txt = fh.read()
            except OSError:
                continue

            for sym_name, def_file in symbol_map.items():
                if def_file != f.relative_path and re.search(r"\b" + re.escape(sym_name) + r"\b", txt):
                    target_file = next((x for x in files if x.relative_path == def_file), None)
                    if target_file and f.relative_path not in target_file.callers:
                        target_file.callers.append(f.relative_path)
