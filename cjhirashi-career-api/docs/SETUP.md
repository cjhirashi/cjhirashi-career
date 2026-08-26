# API REST — Guía de Configuración Local

**DEVELOPER GUIDE**

![Setup Time](https://img.shields.io/badge/setup-~10%20min-informational)
![Difficulty](https://img.shields.io/badge/dificultad-básico-brightgreen)

---

**Prerrequisitos:**
- Python 3.11+
- PostgreSQL 15+ (local o vía Docker)
- Git

---

## 📋 Tabla de Contenidos

- [Instalación](#-instalación)
- [Configuración del Entorno](#-configuración-del-entorno)
- [Inicializar la Base de Datos](#-inicializar-la-base-de-datos)
- [Ejecutar el Servidor](#-ejecutar-el-servidor)
- [Verificación](#-verificación)
- [Configuración de IDE](#-configuración-de-ide)
- [Problemas Comunes de Setup](#-problemas-comunes-de-setup)

---

## 🚀 Instalación

### Paso 1: Crear Entorno Virtual e Instalar Dependencias

```bash
cd api/
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Paso 2: Configurar Variables de Entorno

```bash
cp .env.example .env
```

Edita `.env` con tus valores. Variables mínimas requeridas:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mcp_db
SECRET_KEY=una-clave-aleatoria-de-al-menos-32-caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:8002,http://localhost:8003,http://localhost:8004
```

> **⚠️ Importante**: `SECRET_KEY` debe tener mínimo 32 caracteres. Genera uno seguro con:
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(32))"
> ```

## 🗄️ Inicializar la Base de Datos

### Opción 1: PostgreSQL Local

```bash
psql -U user -d mcp_db -f init.sql
```

### Opción 2: PostgreSQL con Docker

```bash
docker run -d \
  --name postgres-dev \
  -e POSTGRES_USER=mcpuser \
  -e POSTGRES_PASSWORD=mcppass123 \
  -e POSTGRES_DB=mcp_db \
  -p 5432:5432 \
  postgres:15-alpine
```

### Opción 3: Creación automática vía SQLAlchemy

El método `init_db()` en `src/database.py` ejecuta `Base.metadata.create_all()` al arrancar la API, creando las tablas de los modelos que estén importados en el proceso. Ver [DATABASE.md § Estado de las Tablas](./DATABASE.md#-estado-de-las-tablas) para las limitaciones actuales de este mecanismo frente a `init.sql`.

## ▶️ Ejecutar el Servidor

### Desarrollo (con recarga automática)

```bash
cd src/
uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

### Con Docker

```bash
docker build -t portafolio-api:latest .
docker run -p 8001:8001 --env-file .env portafolio-api:latest
```

> **Nota**: el `Dockerfile` actual copia todo el contenido de `api/` a `/app` y ejecuta `uvicorn app:app`, lo cual requiere que el proceso arranque con `src/` como directorio de trabajo (`WORKDIR /app/src` o `--app-dir src`). Si el contenedor falla con `ModuleNotFoundError: No module named 'app'`, ver [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#problema-modulenotfounderror-no-module-named-app-en-docker).

## ✅ Verificación

```bash
curl http://localhost:8001/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "app_name": "cjhirashi-career API",
  "version": "1.0.0"
}
```

Documentación interactiva disponible en `http://localhost:8001/docs` (Swagger UI) y `http://localhost:8001/redoc` (ReDoc).

## 🖥️ Configuración de IDE

### VS Code

1. Instalar la extensión de Python
2. Seleccionar intérprete: `venv/bin/python`
3. Instalar Pylance para verificación de tipos

### PyCharm

1. Configurar el intérprete a `venv/bin/python`
2. Habilitar pytest en las configuraciones de ejecución
3. Marcar `src/` como "Sources Root" para que los imports absolutos (`from config import settings`) resuelvan correctamente

## 🔧 Problemas Comunes de Setup

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `Port 8001 already in use` | Otro proceso usa el puerto | `lsof -i :8001` y `kill -9 <PID>` |
| Error de conexión a BD | PostgreSQL no corre o `DATABASE_URL` incorrecta | Verificar `.env` y que el contenedor/servicio esté activo |
| `ModuleNotFoundError` al importar `config`/`database` | Se ejecutó `uvicorn` fuera de `src/` | Ejecutar `uvicorn app:app` **desde** `src/`, no desde `api/` |

Ver [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) para el listado completo de problemas conocidos.

---

**Relacionado**: [README.md](./README.md) · [DATABASE.md](./DATABASE.md) · [ARCHITECTURE.md](./ARCHITECTURE.md)
