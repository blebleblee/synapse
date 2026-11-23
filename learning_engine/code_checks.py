"""
Static checks of the Python code blocks in a lesson, using only the standard
library (no model calls, no third-party linters).

- PYTHON_SYNTAX_ERROR: a ```python block that does not parse: broken or
  truncated code, or another language (SQL, shell, JavaScript, JSON) tagged
  as Python.
- MISSING_IMPORT: a well-known module name (np, pd, torch, os, Optional, ...)
  used in the lesson but imported nowhere in it. Imports in earlier blocks of
  the same file count, and names the lesson defines itself are never flagged;
  other unknown names are not guessed at.
"""
import ast
import builtins
import re
import warnings
from typing import List, Tuple

_PYTHON_FENCE = re.compile(r"^```(?:python3?|py)[ \t]*\n(.*?)^```", re.MULTILINE | re.DOTALL)

# Name as used in code -> where it is normally imported from.
WELL_KNOWN = {
    "np": "numpy", "pd": "pandas", "plt": "matplotlib.pyplot", "sns": "seaborn", "sp": "scipy",
    "torch": "torch", "nn": "torch.nn", "F": "torch.nn.functional", "tf": "tensorflow",
    "os": "os", "sys": "sys", "json": "json", "time": "time", "re": "re", "math": "math",
    "random": "random", "asyncio": "asyncio", "logging": "logging", "datetime": "datetime",
    "subprocess": "subprocess", "itertools": "itertools", "collections": "collections",
    "hashlib": "hashlib", "threading": "threading", "uuid": "uuid", "struct": "struct",
    "socket": "socket", "shutil": "shutil", "glob": "glob", "pickle": "pickle", "copy": "copy",
    "Path": "pathlib", "Optional": "typing", "List": "typing", "Dict": "typing", "Tuple": "typing",
    "Any": "typing", "Union": "typing", "Callable": "typing", "Iterable": "typing",
    "Sequence": "typing", "dataclass": "dataclasses", "field": "dataclasses", "Enum": "enum",
    "defaultdict": "collections", "Counter": "collections", "deque": "collections",
    "partial": "functools", "tqdm": "tqdm", "requests": "requests", "yaml": "yaml",
}


class _Names(ast.NodeVisitor):
    """Names a block binds anywhere (any scope) and names it reads."""

    def __init__(self) -> None:
        self.bound: set = set()
        self.used: set = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.bound.add((alias.asname or alias.name).split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.bound.add(alias.asname or alias.name)

    def _bind_args(self, args: ast.arguments) -> None:
        for a in args.posonlyargs + args.args + args.kwonlyargs:
            self.bound.add(a.arg)
        for a in (args.vararg, args.kwarg):
            if a:
                self.bound.add(a.arg)

    def visit_FunctionDef(self, node) -> None:
        self.bound.add(node.name)
        self._bind_args(node.args)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._bind_args(node.args)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.bound.add(node.name)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.bound.add(node.name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        (self.used if isinstance(node.ctx, ast.Load) else self.bound).add(node.id)


def check_python_blocks(markdown: str) -> List[Tuple[str, str]]:
    """(code, message) for each problem in the lesson's Python blocks."""
    problems: List[Tuple[str, str]] = []
    names = _Names()
    for block in _PYTHON_FENCE.findall(markdown):
        if ">>>" in block:  # interactive session: prompts and output, not a program
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)  # e.g. "\d" in a plain string
                tree = ast.parse(block)
        except SyntaxError as e:
            snippet = (e.text or "").strip()[:60]
            problems.append(("PYTHON_SYNTAX_ERROR",
                             f"Python block does not parse (line {e.lineno}: {e.msg})"
                             + (f": {snippet}" if snippet else "")
                             + ". Broken or truncated code, or another language tagged as Python."))
            continue
        names.visit(tree)
    for name in sorted(names.used - names.bound):
        if name in WELL_KNOWN and not hasattr(builtins, name):
            problems.append(("MISSING_IMPORT", f"'{name}' is used but never imported in this lesson "
                                               f"(from {WELL_KNOWN[name]})"))
    return problems
