# API REST — Portafolio-cjhirashi — Troubleshooting Guide

**TROUBLESHOOTING**

![Status](https://img.shields.io/badge/status-en%20actualización-yellow)

---

**Ayuda Rápida:**
- [Docker: ModuleNotFoundError al arrancar](#problema-modulenotfounderror-no-module-named-app-en-docker)
- [Conexión a base de datos](#problema-no-se-puede-conectar-a-postgresql)
- [401 Unauthorized](#problema-401-unauthorized-credenciales-inválidas)
- [Modo Debug](#-modo-debug)
- [Cuándo Contactar Soporte](#-cuándo-contactar-soporte)

---

## 📋 Tabla de Contenidos

- [Problemas Más Comunes](#-problemas-más-comunes)
- [Códigos de Error de la API](#-códigos-de-error-de-la-api)
- [Modo Debug](#-modo-debug)
- [FAQ](#-faq)
- [Cuándo Contactar Soporte](#-cuándo-contactar-soporte)

---

## ⚠️ Problemas Más Comunes

### Problema: `ModuleNotFoundError: No module named 'app'` en Docker

**Síntoma**:
```
ModuleNotFoundError: No module named 'app'
```
al arrancar el contenedor con `docker run` o `docker compose up`.

**Causa Raíz**: el `Dockerfile` copia todo `api/` a `/app` (`COPY . .`) y ejecuta `CMD ["uvicorn", "app:app", ...]` esperando un `app.py` en `/app`. El archivo real está en `/app/src/app.py`.

**Solución**:

1. Ejecutar uvicorn indicando el subdirectorio de la app:
   ```bash
   uvicorn src.app:app --host 0.0.0.0 --port 8001
   ```
2. O, para no cambiar el import interno (`from config import settings`, imports absolutos relativos a `src/`), usar `--app-dir src`:
   ```bash
   uvicorn app:app --app-dir src --host 0.0.0.0 --port 8001
   ```

**Verificación**: `curl http://localhost:8001/health` debe responder `{"status": "healthy", ...}`.

**Nota**: esta es una discrepancia real entre `Dockerfile` y la estructura de `src/` — repórtala al responsable de infraestructura (Experto Docker) para corregir el `Dockerfile` de forma permanente en vez de aplicar el workaround en cada ejecución.

---

### Problema: No se puede conectar a PostgreSQL

**Síntoma**:
```
psycopg2.OperationalError: could not translate host name "postgres" to address
```
o
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Causa Raíz**: el contenedor de PostgreSQL no está corriendo, o `DATABASE_URL` apunta a un host incorrecto (`postgres` es válido solo dentro de la red Docker; en desarrollo local fuera de Docker debe ser `localhost`).

**Solución**:

1. Verificar que PostgreSQL esté activo:
   ```bash
   docker ps | grep postgres
   ```
2. Si no está corriendo, iniciarlo:
   ```bash
   docker run -d --name postgres-dev -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15-alpine
   ```
3. Revisar `DATABASE_URL` en `.env`:
   ```bash
   # Local (fuera de Docker)
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mcp_db
   # Dentro de Docker Compose
   DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/mcp_db
   ```

**Verificación**: `psql -U user -d mcp_db -c "SELECT 1;"` debe ejecutarse sin error.

---

### Problema: 401 Unauthorized (Credenciales Inválidas)

**Síntoma**:
```json
{"detail": "Credenciales inválidas"}
```
al hacer `POST /auth/login`.

**Causa Raíz**: username inexistente, contraseña incorrecta, o el usuario fue creado antes de que el esquema de `users` incluyera todas sus columnas actuales (ver [DATABASE.md § Estado de las Tablas](./DATABASE.md#-estado-de-las-tablas)).

**Solución**:

1. Confirmar que el usuario existe:
   ```bash
   psql -U user -d mcp_db -c "SELECT id, username FROM users;"
   ```
2. Probar el endpoint directamente:
   ```bash
   curl -X POST http://localhost:8001/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"usuario","password":"password123"}'
   ```
3. Si el usuario no existe, registrarlo primero con `POST /auth/register`.

**Verificación**: la respuesta debe incluir `access_token` con status `200`.

**¿Sigue sin funcionar?** → Revisar que `SECRET_KEY` no haya cambiado entre el momento en que se emitió un token previo y el intento actual de usarlo (tokens firmados con una `SECRET_KEY` anterior dejan de ser válidos).

---

### Problema: `422 Unprocessable Entity` al registrar usuario

**Síntoma**:
```json
{"detail": "Error de validación", "errors": [...]}
```

**Causa Raíz**: datos que no cumplen las reglas de `schemas/user.py` (`username` < 3 caracteres, `email` con formato inválido, `password` < 8 caracteres).

**Solución**:

1. Revisar el detalle de `errors` en la respuesta — indica el campo (`loc`) y el motivo (`msg`).
2. Corregir el payload:
   ```bash
   curl -X POST http://localhost:8001/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"validuser","email":"valido@example.com","password":"password123"}'
   ```

**Verificación**: respuesta `201 Created` con el usuario creado.

---

### Problema: Puerto 8001 ya en uso

**Síntoma**:
```
[Errno 98] Address already in use
```

**Causa Raíz**: otro proceso (posiblemente una instancia anterior de uvicorn) ya escucha en el puerto 8001.

**Solución**:

1. Identificar el proceso:
   ```bash
   lsof -i :8001
   ```
2. Terminarlo:
   ```bash
   kill -9 <PID>
   ```
3. O usar un puerto distinto temporalmente:
   ```bash
   uvicorn app:app --port 8011
   ```

**Verificación**: `curl http://localhost:8001/health` responde sin error de conexión.

## 🔴 Códigos de Error de la API

| Código | Significado | Causa Común | Solución |
|--------|-------------|-------------|----------|
| 400 | Bad Request | Username/email duplicado | Usar credenciales distintas |
| 401 | Unauthorized | Token ausente/expirado o credenciales inválidas | Login nuevamente |
| 404 | Not Found | Documento no existe o pertenece a otro usuario | Verificar `document_id` y token |
| 422 | Unprocessable Entity | Payload no cumple el schema Pydantic | Revisar `errors` en la respuesta |
| 500 | Internal Server Error | Excepción no controlada | Revisar logs del contenedor |

## 🐛 Modo Debug

### Habilitar logging detallado

```bash
# En .env
DEBUG=true
```

Con `DEBUG=true`, `database.py` habilita `echo=True` en el engine de SQLAlchemy (loguea cada SQL ejecutado) y `app.py` sube el nivel de logging a `DEBUG`.

### Ver logs del contenedor

```bash
docker logs mcp_api -f
```

### Debugger interactivo (Python)

```python
import pdb; pdb.set_trace()
```

## ❓ FAQ

**P: ¿Cómo genero un `SECRET_KEY` seguro?**
R: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

**P: ¿Por qué `/auth/refresh` no existe si el schema `TokenRefreshRequest` sí está definido?**
R: El schema existe, pero la ruta que lo usa (`routes/auth_enhanced.py`) no está registrada en `app.py` todavía. Ver [ARCHITECTURE.md § Deuda Técnica](./ARCHITECTURE.md#-deuda-técnica-conocida).

**P: ¿Puedo consultar `/identity` o `/competencies`?**
R: No, esos routers no existen aún. Ver [API.md § Endpoints en Diseño](./API.md#-endpoints-en-diseño-no-implementados).

**P: ¿Dónde veo la documentación interactiva de la API?**
R: `http://localhost:8001/docs` (Swagger UI) o `http://localhost:8001/redoc`.

## 📞 Cuándo Contactar Soporte

Escala el problema si:

- El error persiste después de aplicar los pasos de esta guía
- Sospechas de un problema de seguridad (credenciales expuestas, acceso indebido a datos de otro usuario)
- El contenedor entra en crash loop sin mensaje de error claro en los logs

**Contacto**: cjhirashi@gmail.com

**Antes de escribir, recopila:**
1. Comando exacto ejecutado y su salida completa
2. Logs recientes: `docker logs mcp_api --tail 100`
3. Contenido de `.env` **sin** `SECRET_KEY` ni contraseñas
4. Versión de Python y de las dependencias relevantes (`pip freeze | grep -i fastapi`)

---

**Relacionado**: [SETUP.md](./SETUP.md) · [ARCHITECTURE.md](./ARCHITECTURE.md) · [DATABASE.md](./DATABASE.md)
