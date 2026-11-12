# API REST — cjhirashi-career — Guía de testing

**TESTING GUIDE** · **Última actualización**: 2026-11-05

Estrategia y ejecución de las pruebas de la API. Estado medido el 2026-11-05: **867 pruebas** en 93 archivos (`pytest --collect-only`). Objetivo de cobertura: **80 %**, impuesto por `pytest.ini` (`--cov-fail-under=80`): una corrida parcial o solo de recolección falla ese umbral sin que haya un defecto.

## Estructura

```
tests/
├── conftest.py     # fixtures compartidas
├── unit/           # servicios, middleware, Bedrock (unit/bedrock/), migraciones, analítica del portafolio
├── integration/    # rutas de autenticación y flujos HTTP completos
└── fixtures/       # datos de apoyo
```

Los marcadores (`--strict-markers`) son `unit`, `integration`, `slow`, `asyncio` y `requisito`. Cada prueba de una feature del arnés anota su requisito: `@pytest.mark.requisito("RF-014")`.

## Ejecutar

```bash
cd cjhirashi-career-api
venv_test/bin/python -m pytest -q                       # suite completa con cobertura
venv_test/bin/python -m pytest tests/unit/bedrock -q    # un subconjunto (CI corre este)
venv_test/bin/python -m pytest tests/unit/test_auth.py -k login -q
```

Los `venv*` pueden no existir en un clon limpio: `python -m venv venv_test && venv_test/bin/pip install -r requirements.txt pytest pytest-asyncio httpx aiosqlite`. El CI (`.github/workflows/ci.yml`) corre `tests/unit/bedrock` con Python 3.11 y SQLite en memoria.

### Base de datos de pruebas

- **Por defecto**, SQLite en memoria (`conftest.py` mapea `JSONB` a `JSON` solo en SQLite). Las pruebas que dependen de secuencias de IDs prefijados (`usr-1`, `psp-1`…) se saltan.
- **Con Postgres real**: define `TEST_DATABASE_URL` apuntando a una base **desechable** (nunca la de desarrollo ni la de producción):

```bash
docker run -d --rm --name career-testdb -e POSTGRES_PASSWORD=test -p 127.0.0.1:55432:5432 postgres:15-alpine
export TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@127.0.0.1:55432/postgres
```

## Fixtures (`conftest.py`)

`test_db` (esquema limpio por prueba), `db_session`, `test_user` y `test_user_data`, `test_identity`, `test_competency`, `valid_login_credentials` / `invalid_login_credentials`, `valid_jwt_token` y `async_client` (httpx sobre la app, con `get_db` sustituido).

## Cómo escribir una prueba

1. Elige la capa: `unit/` si prueba un servicio o módulo aislado; `integration/` si recorre la ruta HTTP.
2. Anota el requisito (`@pytest.mark.requisito("RF-NNN")`) y escribe primero la prueba en rojo.
3. Sin red ni servicios externos: AWS Bedrock, MinIO y los proveedores de vacantes se simulan.
4. Las pruebas son `async` (`asyncio_mode = auto`); no necesitan decorador.

## Cobertura

`--cov=src` con informe en `htmlcov/` y términos faltantes en consola. El último `coverage.json` versionado es de 2026-08-17 (78,4 %) y está obsoleto; la medición vigente sale de una corrida completa.

## Depuración

`pytest -x --pdb` se detiene en el primer fallo; `-k <expresión>` filtra; `-s` muestra la salida estándar. Si una prueba de base de datos se salta, comprueba `TEST_DATABASE_URL`.

---

**Relacionado**: [README.md](./README.md) · [../tests/README.md](../tests/README.md) · [../../docs/08-CROSSCUTTING-CONCEPTS.md](../../docs/08-CROSSCUTTING-CONCEPTS.md)
