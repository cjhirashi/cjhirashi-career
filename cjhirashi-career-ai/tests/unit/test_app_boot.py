"""RF-008 / RF-002: arranque de la app, carga de routers y /health (T-012)."""
import ast
import importlib
import pkgutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[2] / "src"


def _router_modules():
    import routes

    return [m.name for m in pkgutil.iter_modules(routes.__path__)]


def _unregistered(app, modules):
    """Módulos de routes/ cuyo `router` no está incluido en `app` (include_router)."""
    # FastAPI recientes envuelven los routers incluidos en _IncludedRouter(original_router=...);
    # las versiones anteriores (0.104) aplanan las rutas en app.routes.
    included = [getattr(r, "original_router", None) for r in app.routes]
    flat = {(r.path, frozenset(r.methods)) for r in app.routes if hasattr(r, "methods")}
    missing = []
    for name in modules:
        module = importlib.import_module(f"routes.{name}")  # ImportError -> falla el test
        router = getattr(module, "router", None)
        assert router is not None, f"routes/{name}.py no expone `router`"
        wrapped = any(router is inc for inc in included)
        flattened = bool(router.routes) and all(
            (r.path, frozenset(r.methods)) in flat for r in router.routes
        )
        if not (wrapped or flattened):
            missing.append(name)
    return missing


@pytest.mark.requisito("RF-008")
def test_every_router_module_imports_and_is_registered():
    """Hazard del ImportError silenciado: cada routes/*.py debe importar y estar en la app."""
    from app import app

    modules = _router_modules()
    assert modules, "routes/ no contiene ningún router"
    assert _unregistered(app, modules) == []


@pytest.mark.requisito("RF-008")
def test_app_does_not_swallow_import_errors():
    tree = ast.parse((SRC / "app.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                names = ast.dump(handler.type) if handler.type else "bare"
                assert "ImportError" not in names and "ModuleNotFoundError" not in names and names != "bare", (
                    "app.py no puede silenciar ImportError al registrar routers"
                )


@pytest.mark.requisito("RF-008")
def test_unregistered_router_is_detected():
    """Meta-test: la comprobación falla si una app no registra un router existente."""
    from fastapi import FastAPI

    assert _unregistered(FastAPI(), ["health"]) == ["health"]


@pytest.mark.requisito("RF-002")
def test_health_is_public_and_ok():
    from app import app

    resp = TestClient(app).get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.requisito("RF-002")
def test_unknown_route_is_404():
    from app import app

    assert TestClient(app).get("/no-existe").status_code == 404
