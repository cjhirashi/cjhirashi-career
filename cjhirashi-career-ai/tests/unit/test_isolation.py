"""RF-003: el harness no toca career_db ni Qdrant (T-040).

Escaneo AST de `src/`: identificadores, imports y literales de cadena (no docstrings ni
comentarios) no pueden referirse a `career_db`, `qdrant`, variables `SOURCE_*` ni `psycopg`
(la copia desde otra BD vive fuera de `src/`, en `scripts/`).
Límite: una cadena armada dinámicamente (p. ej. por concatenación) no se detecta.
"""
import ast
import re
from pathlib import Path
from typing import Iterator, List

import pytest

pytestmark = pytest.mark.requisito("RF-003")

SRC = Path(__file__).resolve().parents[2] / "src"
_SOURCE_VAR = re.compile(r"(?<![A-Za-z0-9])SOURCE_[A-Z0-9_]+")
_SIMPLE = re.compile(r"career_db|qdrant|psycopg", re.IGNORECASE)


def _is_forbidden(text: str) -> bool:
    return bool(_SIMPLE.search(text) or _SOURCE_VAR.search(text))


def _docstring_nodes(tree: ast.AST) -> set:
    nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
                nodes.add(id(body[0].value))
    return nodes


def _tokens(tree: ast.AST) -> Iterator[str]:
    docs = _docstring_nodes(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            yield node.module or ""
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, ast.Attribute):
            yield node.attr
        elif isinstance(node, ast.arg):
            yield node.arg
        elif isinstance(node, ast.keyword) and node.arg:
            yield node.arg
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node.name
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            yield node.value


def scan(root: Path) -> List[str]:
    hits: List[str] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        hits += [f"{path.relative_to(root)}: {t!r}" for t in _tokens(tree) if _is_forbidden(t)]
    return hits


def test_src_has_no_reference_to_career_db_qdrant_or_foreign_db_drivers():
    assert scan(SRC) == []


def test_scanner_flags_violations_and_ignores_docstrings_and_comments(tmp_path):
    (tmp_path / "bad.py").write_text(
        '"""menciona career_db en un docstring"""\n'
        "# comentario con qdrant\n"
        "import psycopg2\n"
        "from qdrant_client import QdrantClient\n"
        'URL = "postgresql://x/career_db"\n'
        'name = "SOURCE_DATABASE_URL"\n'
        "resource_key = 'ok'\n"
    )
    hits = scan(tmp_path)
    joined = "\n".join(hits)
    assert "psycopg2" in joined and "qdrant_client" in joined and "QdrantClient" in joined
    assert "career_db" in joined and "SOURCE_DATABASE_URL" in joined
    assert "resource_key" not in joined and "docstring" not in joined and "comentario" not in joined
