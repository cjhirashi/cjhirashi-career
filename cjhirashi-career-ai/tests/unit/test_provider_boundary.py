"""RF-005 / RNF-001: frontera del SDK de AWS (T-022).

Solo `src/providers/bedrock/` puede importar `boto3`/`botocore`. `services/` y `routes/`
no importan `providers.bedrock`; solo la fábrica de `config.py` lo hace.
"""
import ast
from pathlib import Path
from typing import List, Tuple

import pytest

pytestmark = pytest.mark.requisito("RF-005")

SRC = Path(__file__).resolve().parents[2] / "src"
SDK_ROOTS = {"boto3", "botocore"}
BEDROCK_DIR = Path("providers") / "bedrock"
FACTORY_FILES = {Path("config.py")}


def _imported_modules(tree: ast.AST, package: Tuple[str, ...] = ()) -> List[str]:
    """Módulos importados en cualquier punto del árbol, incluidos imports dentro de
    funciones, los relativos (resueltos a absoluto con `package`, el paquete del archivo
    relativo a `src/`) y los dinámicos con nombre literal (`__import__("x")`, `import_module("x")`).

    Límite conocido: `import_module(nombre_no_literal)` no se puede analizar estáticamente
    y NO se cubre."""
    found: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                base = node.module.split(".") if node.module else []
            else:
                keep = len(package) - (node.level - 1)
                if keep < 0:
                    continue  # sale de src/: no es código nuestro
                base = list(package[:keep]) + (node.module.split(".") if node.module else [])
            if base:
                found.append(".".join(base))
                # `from providers import bedrock` equivale a importar providers.bedrock
                found.extend(".".join(base + [alias.name]) for alias in node.names)
        elif isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name in {"__import__", "import_module"} and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    found.append(arg.value)
    return found


def boundary_violations(root: Path) -> List[str]:
    """Violaciones de la frontera en todos los .py bajo `root`."""
    violations: List[str] = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        inside_bedrock = BEDROCK_DIR in rel.parents or rel.parent == BEDROCK_DIR
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for module in _imported_modules(tree, rel.parent.parts):
            top = module.split(".")[0]
            if top in SDK_ROOTS and not inside_bedrock:
                violations.append(f"{rel}: importa {module} fuera de providers/bedrock/")
            if (
                module == "providers.bedrock" or module.startswith("providers.bedrock.")
            ) and not inside_bedrock and rel not in FACTORY_FILES:
                violations.append(f"{rel}: importa {module} (solo la fábrica de config.py puede)")
    return violations


def test_src_respects_the_provider_boundary():
    assert boundary_violations(SRC) == []


def test_boundary_dir_exists_and_is_the_only_place_with_the_sdk():
    """Evita el verde vacío: el SDK debe estar de verdad dentro de providers/bedrock/."""
    users = []
    for path in sorted((SRC / BEDROCK_DIR).glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if any(m.split(".")[0] in SDK_ROOTS for m in _imported_modules(tree)):
            users.append(path.name)
    assert users, "providers/bedrock/ no importa boto3: la frontera no tiene implementación"


# ---------------------------------------------------------------------------
# Meta-tests: la comprobación FALLA de verdad ante una violación (mismo criterio que T-012)
# ---------------------------------------------------------------------------

def _tree(tmp_path: Path, files: dict) -> Path:
    for rel, body in files.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    "rel, body",
    [
        ("services/x.py", "import boto3\n"),
        ("services/x.py", "from botocore.exceptions import ClientError\n"),
        ("routes/x.py", "def f():\n    import boto3\n"),
        ("services/x.py", "m = __import__('boto3')\n"),
        ("services/x.py", "import importlib\nimportlib.import_module('botocore.stub')\n"),
        ("providers/base.py", "import boto3\n"),
        ("providers/other/x.py", "import boto3\n"),
    ],
)
def test_meta_sdk_import_outside_bedrock_is_detected(tmp_path, rel, body):
    assert boundary_violations(_tree(tmp_path, {rel: body}))


@pytest.mark.parametrize(
    "rel, body",
    [
        ("services/x.py", "from providers.bedrock.converse import BedrockProvider\n"),
        ("routes/x.py", "import providers.bedrock\n"),
        ("services/x.py", "from providers import bedrock\n"),
        ("services/x.py", "from ..providers.bedrock import client\n"),
        ("services/x.py", "from .. import providers\nfrom ..providers import bedrock\n"),
        ("routes/sub/x.py", "from ...providers.bedrock.converse import BedrockProvider\n"),
        ("providers/x.py", "from .bedrock import converse\n"),
        ("providers/x.py", "from . import bedrock\n"),
    ],
)
def test_meta_services_importing_bedrock_provider_is_detected(tmp_path, rel, body):
    assert boundary_violations(_tree(tmp_path, {rel: body}))


def test_meta_allowed_usages_are_not_flagged(tmp_path):
    root = _tree(
        tmp_path,
        {
            "providers/bedrock/client.py": "import boto3\nfrom botocore.exceptions import ClientError\n",
            "providers/bedrock/converse.py": "from providers.bedrock.client import get_client\n",
            "config.py": "def get_provider():\n    from providers.bedrock import BedrockProvider\n",
            "services/x.py": "from providers.base import ModelProvider\nfrom . import y\nfrom .y import z\n",
            "providers/bedrock/pricing.py": "from . import client\nfrom ..base import Usage\n",
        },
    )
    assert boundary_violations(root) == []
