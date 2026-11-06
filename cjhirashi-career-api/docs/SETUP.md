# API REST — Guía de configuración local

**DEVELOPER GUIDE** · **Última actualización**: 2026-11-05

**Prerrequisitos:** Python 3.11+ (la imagen usa 3.11), PostgreSQL 15 (local o en Docker) y Git. Para ejecutar todo el sistema, Docker Compose: [../../docs/07-DEPLOYMENT-VIEW.md](../../docs/07-DEPLOYMENT-VIEW.md).

## 1. Instalar

```bash
cd cjhirashi-career-api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

## 2. Configurar el entorno

```bash
cp .env.example .env
```

La plantilla raíz del repo (`../.env.example`) lista todas las variables; las mínimas para arrancar la API son:

```bash
DATABASE_URL=postgresql+asyncpg://career_admin:<contraseña>@localhost:5432/career_db
SECRET_KEY=<32+ caracteres aleatorios>
CORS_ORIGINS=http://localhost:8002,http://localhost:8003
MINIO_ENDPOINT=localhost:9000
MINIO_ROOT_USER=<usuario>
MINIO_ROOT_PASSWORD=<contraseña>
MINIO_BUCKET=cjhirashi-career
MINIO_PUBLIC_URL=http://localhost:9000/cjhirashi-career
```

> `SECRET_KEY` debe tener al menos 32 caracteres: `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Si MinIO no responde al arrancar, la API lo registra y sigue sirviendo todo menos los archivos (subida, listado y descarga fallan hasta que MinIO esté accesible). Variables completas y política de secretos: [../../docs/ENVIRONMENT-SECURITY.md](../../docs/ENVIRONMENT-SECURITY.md).

## 3. Base de datos

PostgreSQL local o desechable en Docker:

```bash
docker run -d --name career-pg-dev -e POSTGRES_USER=career_admin -e POSTGRES_PASSWORD=<contraseña> \
  -e POSTGRES_DB=career_db -p 127.0.0.1:5432:5432 postgres:15-alpine
```

Aplica el esquema con **Alembic** (fuente de verdad para despliegues):

```bash
alembic upgrade head          # desde cjhirashi-career-api/
```

`init_db()` (`src/database.py`) ejecuta además `Base.metadata.create_all` y crea las secuencias de IDs prefijados al arrancar, pero **no** sustituye a las migraciones. `init.sql` es histórico (anterior a 2026-08-21, cuando Alembic no trackeaba nada). Detalle: [DATABASE.md](./DATABASE.md) y [../alembic/README.md](../alembic/README.md).

## 4. Ejecutar

```bash
uvicorn app:app --app-dir src --reload --host 0.0.0.0 --port 8000
```

Con Docker (desde la raíz del repo): `docker compose up -d --build api` (imagen `python:3.11-slim`, un worker, healthcheck en `/health`). La API no publica puerto al host; se alcanza por la red `net-cjhirashi-career`.

## 5. Verificar

```bash
curl http://localhost:8000/health        # {"status":"healthy","app_name":…,"version":…}
curl http://localhost:8000/system/readiness
```

Swagger UI en `http://localhost:8000/docs` y ReDoc en `/redoc`. Pruebas: [TESTING.md](./TESTING.md).

## IDE

Intérprete `venv/bin/python`; marca `src/` como *Sources Root* (los imports son absolutos: `from config import settings`); habilita pytest.

## Problemas comunes

| Síntoma | Causa | Solución |
|---|---|---|
| `Port 8000 already in use` | Otro proceso usa el puerto | `lsof -i :8000` y detén el proceso |
| Error de conexión a la BD | PostgreSQL no corre o `DATABASE_URL` incorrecta | Revisa `.env` y que el contenedor esté activo |
| Los archivos fallan (el resto de la API sirve) | `MINIO_ENDPOINT` apunta a `localhost` dentro de Docker o MinIO no responde | En Compose debe ser `minio:9000`; en local, un MinIO accesible. El log del arranque dice «Failed to initialize MinIO bucket» |
| `ModuleNotFoundError` al importar `config` o `database` | `uvicorn` sin `--app-dir src` | Usa el comando de arriba |

Más casos: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

---

**Relacionado**: [README.md](./README.md) · [DATABASE.md](./DATABASE.md) · [ARCHITECTURE.md](./ARCHITECTURE.md)
