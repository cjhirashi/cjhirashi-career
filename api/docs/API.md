# API REST — Portafolio-cjhirashi — API Reference

**API REFERENCE**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Status](https://img.shields.io/badge/status-desarrollo%20activo-yellow)
![Auth](https://img.shields.io/badge/auth-JWT%20Bearer-orange)

---

**URL Base (desarrollo local)**: `http://localhost:8001`
**URL Base (interno en Docker)**: `http://mcp_api:8001` (solo accesible desde `network-cjhirashi-srv`)
**Última actualización**: 2026-08-16

---

## 📋 Tabla de Contenidos

- [Autenticación](#-autenticación)
- [Endpoints de Autenticación](#-endpoints-de-autenticación)
- [Endpoints de Documentos](#-endpoints-de-documentos)
- [Health Check](#-health-check)
- [Manejo de Errores](#-manejo-de-errores)
- [Paginación](#-paginación)
- [Ejemplos](#-ejemplos)
- [Endpoints en Diseño (No Implementados)](#-endpoints-en-diseño-no-implementados)

---

> **Nota de alcance**: este documento describe únicamente los endpoints registrados y funcionales en `src/app.py` (routers `auth` y `documents`). Para el estado de otros dominios de datos (identidad, competencias, evidencia, carrera), ver [Endpoints en Diseño](#-endpoints-en-diseño-no-implementados).

## 🔐 Autenticación

Autenticación mediante JWT Bearer Token, algoritmo HS256, emitido por `POST /auth/login`.

```bash
curl http://localhost:8001/documents \
  -H "Authorization: Bearer <access_token>"
```

El token expira en `ACCESS_TOKEN_EXPIRE_DAYS` días (7 por defecto, configurable vía variable de entorno). No existe endpoint de refresh activo — al expirar, el usuario debe hacer login nuevamente. Ver [SECURITY.md](./SECURITY.md) para el detalle de implementación.

## 🔑 Endpoints de Autenticación

Prefijo: `/auth`

### POST /auth/register

**Descripción**: Registra un nuevo usuario
**Autenticación**: No requerida

**Request Body:**
```json
{
  "username": "usuario",
  "email": "usuario@example.com",
  "password": "password123"
}
```

**Respuesta (201 Created):**
```json
{
  "id": 2,
  "username": "usuario",
  "email": "usuario@example.com",
  "created_at": "2026-08-16T10:00:00Z"
}
```

**Códigos de Estado:**
- 201 — Usuario creado
- 400 — Username o email ya registrado
- 422 — Error de validación (username < 3 caracteres, email inválido, password < 8 caracteres)

### POST /auth/login

**Descripción**: Autentica un usuario y emite un token JWT
**Autenticación**: No requerida

**Request Body:**
```json
{
  "username": "usuario",
  "password": "password123"
}
```

**Respuesta (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": 1,
    "username": "usuario",
    "email": "usuario@example.com",
    "created_at": "2026-08-16T10:00:00Z"
  }
}
```

**Códigos de Estado:**
- 200 — Login exitoso
- 401 — Credenciales inválidas

### POST /auth/logout

**Descripción**: Endpoint informativo — con JWT stateless, la invalidación real ocurre eliminando el token en el cliente
**Autenticación**: No requerida

**Respuesta (200 OK):**
```json
{
  "message": "Logout exitoso. Elimina el token del cliente."
}
```

## 📄 Endpoints de Documentos

Prefijo: `/documents` · Todos requieren `Authorization: Bearer <token>`

### GET /documents

**Descripción**: Lista documentos del usuario autenticado, paginados

**Query Params:**
- `skip` (int, default: 0)
- `limit` (int, default: 100, max: 500)

**Respuesta (200 OK):**
```json
{
  "total": 2,
  "documents": [
    {
      "id": 1,
      "user_id": 1,
      "type": "cv",
      "title": "CV Profesional",
      "data": { "nombre": "Juan Pérez" },
      "created_at": "2026-08-16T10:00:00Z",
      "updated_at": "2026-08-16T10:00:00Z"
    }
  ]
}
```

### GET /documents/{document_id}

**Descripción**: Obtiene un documento específico, validando que pertenezca al usuario

**Códigos de Estado:**
- 200 — Documento encontrado
- 404 — No existe o no pertenece al usuario

### POST /documents

**Descripción**: Crea un documento nuevo para el usuario autenticado

**Request Body:**
```json
{
  "type": "cv",
  "title": "Mi CV",
  "data": { "nombre": "John Doe", "email": "john@example.com" }
}
```

**Respuesta (201 Created)**: objeto `Document` creado

### PUT /documents/{document_id}

**Descripción**: Actualiza campos de un documento existente (`type`, `title`, `data` — todos opcionales)

**Códigos de Estado:**
- 200 — Actualizado
- 404 — No existe o no pertenece al usuario

### DELETE /documents/{document_id}

**Descripción**: Elimina un documento

**Códigos de Estado:**
- 204 — Eliminado (sin contenido)
- 404 — No existe o no pertenece al usuario

### GET /documents/type/{doc_type}

**Descripción**: Lista documentos del usuario filtrados por tipo (ej. `cv`, `cover_letter`), con la misma paginación que `GET /documents`

## 🩺 Health Check

### GET /health

**Descripción**: Estado de la API, usado por el `HEALTHCHECK` de Docker
**Autenticación**: No requerida

**Respuesta (200 OK):**
```json
{
  "status": "healthy",
  "app_name": "Portafolio-cjhirashi API",
  "version": "1.0.0"
}
```

## ❌ Manejo de Errores

| Código | Significado | Causa Típica |
|--------|--------------|--------------|
| 400 | Bad Request | Username/email duplicado en registro |
| 401 | Unauthorized | Token ausente, inválido o expirado; credenciales incorrectas |
| 404 | Not Found | Recurso no existe o pertenece a otro usuario |
| 422 | Unprocessable Entity | Error de validación Pydantic |
| 500 | Internal Server Error | Excepción no controlada (ver logs) |

**Formato de error de validación (422):**
```json
{
  "detail": "Error de validación",
  "errors": [
    { "loc": ["body", "password"], "msg": "ensure this value has at least 8 characters" }
  ]
}
```

**Formato de error genérico (401/404/400):**
```json
{
  "detail": "Mensaje descriptivo del error"
}
```

## 📑 Paginación

Todos los endpoints de listado aceptan `skip` y `limit`:

```
GET /documents?skip=0&limit=50
```

**Respuesta:**
```json
{
  "total": 120,
  "documents": [ "..." ]
}
```

## 💡 Ejemplos

### Flujo completo con cURL

```bash
# 1. Registrar usuario
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"usuario","email":"usuario@example.com","password":"password123"}'

# 2. Login y captura de token
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"usuario","password":"password123"}' \
  | jq -r '.access_token')

# 3. Crear documento
curl -X POST http://localhost:8001/documents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"cv","title":"Mi CV","data":{"nombre":"Test"}}'

# 4. Listar documentos
curl http://localhost:8001/documents \
  -H "Authorization: Bearer $TOKEN"
```

### Python (httpx)

```python
import httpx

response = httpx.post(
    "http://localhost:8001/auth/login",
    json={"username": "usuario", "password": "password123"}
)
token = response.json()["access_token"]

docs = httpx.get(
    "http://localhost:8001/documents",
    headers={"Authorization": f"Bearer {token}"}
)
print(docs.json())
```

## 🔎 Job Discovery (JWT)

Preview-then-save. `run` e `import-url` no escriben `vacancies`.

- `GET /career/job-discoveries/providers`
- `POST /career/job-discoveries/run` — body: `query`, `location`, `providers` (`indeed`, `linkedin`, `getonboard`, `remotive`, `remoteok`), `include_company_boards`, `target_role_id`
- `POST /career/job-discoveries/import-url` — body: `{ "url": "https://www.linkedin.com/jobs/view/…" }`
- `POST /career/job-discoveries/save` — persiste listings `listing_kind=job` como vacantes `pending_review`

Indeed usa Adzuna (`ADZUNA_APP_ID` / `ADZUNA_APP_KEY`). LinkedIn solo devuelve URLs de `linkedin.com/jobs/search`. Ver [ADR-011](../docs/09-DECISIONS/011-job-discovery-adapters.md).

## 🗺️ Endpoints en Diseño (No Implementados)

Los siguientes dominios tienen **modelo de datos y schema Pydantic definidos** (ver [DATABASE.md](./DATABASE.md)), pero **no tienen rutas HTTP registradas** en `src/app.py` todavía. No están disponibles en ningún ambiente:

- Identidad profesional (`Identity`)
- Competencias (`Competency`)
- Evidencia (`Evidence`)
- Estrategias de búsqueda de empleo (`JobStrategy`)
- Vacantes (`Vacancy`)
- Entrevistas (`Interview`)
- Contactos de networking (`NetworkingContact`)
- Métricas (`Metrics`)

Adicionalmente, `src/routes/auth_enhanced.py` implementa un flujo de login/refresh/cambio de contraseña más completo (vía `AuthService` y `UserRepository`), pero **no está incluido** en `app.include_router(...)` — no es accesible mientras no se registre.

---

**Documentación interactiva**: `http://localhost:8001/docs` (Swagger UI) · `http://localhost:8001/redoc`
**Relacionado**: [ARCHITECTURE.md](./ARCHITECTURE.md) · [SECURITY.md](./SECURITY.md) · [DATABASE.md](./DATABASE.md)
