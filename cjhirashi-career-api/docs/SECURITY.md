# API REST — cjhirashi-career — Modelo de Seguridad

**SECURITY**

![Auth](https://img.shields.io/badge/auth-JWT%20HS256-orange)
![Hashing](https://img.shields.io/badge/passwords-bcrypt-green)

---

Implementación de seguridad de la API: autenticación JWT, hashing de contraseñas, aislamiento de datos por usuario y validación de entrada.

---

## 📋 Tabla de Contenidos

- [Autenticación JWT](#-autenticación-jwt)
- [Seguridad de Contraseñas](#-seguridad-de-contraseñas)
- [Aislamiento por Usuario](#-aislamiento-por-usuario)
- [Validación de Entrada](#-validación-de-entrada)
- [Prevención de SQL Injection](#-prevención-de-sql-injection)
- [CORS](#-cors)
- [Variables de Entorno y Secretos](#-variables-de-entorno-y-secretos)
- [Deuda Técnica de Seguridad](#-deuda-técnica-de-seguridad)
- [Checklist de Producción](#-checklist-de-producción)

---

## 🔐 Autenticación JWT

**Algoritmo**: HS256
**Expiración**: `ACCESS_TOKEN_EXPIRE_DAYS` (7 días por defecto, configurable)
**Payload**: `{"sub": <username>, "exp": <timestamp>, "iat": <timestamp>}`

Implementado en `src/utils/security.py` y consumido por `src/middleware/auth.py` (dependency `get_current_user`), usado por todas las rutas del router `documents`.

```python
# Emisión (routes/auth.py)
access_token = create_access_token(data={"sub": user.username})

# Validación (middleware/auth.py)
payload = decode_access_token(token)
username = payload.get("sub")
```

```mermaid
graph LR
    classDef backend fill:#042f2e,stroke:#10b981,color:#fff
    classDef secrets fill:#111827,stroke:#6b7280,color:#fff
    classDef postgres fill:#1e1b4b,stroke:#6366f1,color:#fff
    classDef client fill:#1e293b,stroke:#cbd5e1,color:#fff

    User["👤 Cliente"] -->|username, password| Login["POST /auth/login"]
    Login --> Verify["verify_password()"]
    Verify --> DB["🗄️ users.password_hash"]
    DB -->|Coincide| Create["create_access_token()"]
    Create -->|access_token| User

    User -->|Bearer token| Protected["GET /documents"]
    Protected --> Decode["decode_access_token()"]
    Decode -->|sub = username| Lookup["Buscar usuario en BD"]
    Lookup -->|200| Response["Respuesta autorizada"]

    class Login backend
    class Protected backend
    class Create secrets
    class Decode secrets
    class DB postgres
    class User client
```

## 🔒 Seguridad de Contraseñas

**Hashing**: bcrypt vía `passlib.context.CryptContext(schemes=["bcrypt"])`

```python
hashed = hash_password(plain_password)          # Registro
valid = verify_password(plain_password, hashed)  # Login
```

Nunca se almacena ni se registra en logs la contraseña en texto plano.

## 🧱 Aislamiento por Usuario

Todas las consultas al recurso `documents` filtran explícitamente por el `user_id` del token autenticado — no existe forma de acceder a datos de otro usuario a través de la API:

```python
# repositories: cada query incluye el filtro de propiedad
stmt = select(Document).where(
    Document.id == document_id,
    Document.user_id == current_user.id
)
```

Un `document_id` de otro usuario retorna `404 Not Found`, no `403 Forbidden` — esto evita revelar la existencia del recurso a usuarios no autorizados.

## ✅ Validación de Entrada

Pydantic v2 valida tipo, longitud y formato en cada request:

```python
class UserCreate(UserBase):
    password: constr(min_length=8, max_length=255)

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
```

Errores de validación retornan `422` con el detalle de campo y motivo (ver [API.md § Manejo de Errores](./API.md#-manejo-de-errores)).

## 🛡️ Prevención de SQL Injection

Todo acceso a datos pasa por SQLAlchemy ORM con queries parametrizadas — no hay SQL crudo interpolado con datos de usuario en el código actual:

```python
# Seguro — parametrizado por SQLAlchemy
stmt = select(User).where(User.username == username)
```

## 🌐 CORS

Orígenes permitidos configurados vía `CORS_ORIGINS` (variable de entorno, parseada a lista en `config.py`). Por defecto:

```
http://localhost:8002  (Admin Panel)
http://localhost:8003  (Portal Público)
http://localhost:8004  (MCP Server)
```

## 🔑 Variables de Entorno y Secretos

```bash
# .env (NO se versiona, está en .gitignore)
SECRET_KEY=clave-real-de-producción-min-32-caracteres
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/db

# .env.example (sí se versiona, solo placeholders)
SECRET_KEY=your-secret-key-change-in-production-min-32-chars-recommended
```

## ⚠️ Deuda Técnica de Seguridad

- **Dos implementaciones de autenticación en paralelo**: `utils/security.py` (funciones sueltas, usado por `routes/auth.py`, registrado) y `services/auth_service.py` (clase `AuthService`, usado por `routes/auth_enhanced.py`, **no registrado**). El primero codifica `sub` como `username`; el segundo lo codifica como `str(user.id)`. Si en el futuro se registra `auth_enhanced.py` sin ajustar `middleware/auth.py` (que busca el usuario por `username`), los tokens emitidos por ese router no serán válidos contra el middleware actual.
- **Sin rate limiting activo**: la configuración (`RATE_LIMIT_ENABLED`, `RATE_LIMIT_REQUESTS`) existe en `config.py` pero no hay middleware que la aplique todavía.
- **Sin rotación de refresh tokens**: el modelo `RefreshToken` está definido en base de datos pero no hay lógica de emisión/revocación conectada a un endpoint activo.
- **Sin headers de seguridad HTTP** (`Content-Security-Policy`, `X-Frame-Options`, `Strict-Transport-Security`) configurados en el middleware.

## 📋 Checklist de Producción

- [ ] `SECRET_KEY` rotado a un valor aleatorio fuerte (no el de `.env.example`)
- [ ] `DEBUG=false`
- [ ] HTTPS vía reverse proxy (Caddy, según arquitectura de `cjhirashi-srv`)
- [ ] Backups de base de datos configurados y probados
- [ ] `CORS_ORIGINS` restringido a los tres orígenes internos reales
- [ ] Rate limiting implementado y habilitado
- [ ] Resolver la duplicidad de `auth.py` / `auth_enhanced.py` antes de exponer refresh tokens
- [ ] Auditoría (`audit_logs`) conectada a las rutas de escritura

---

**Referencias**: [OWASP Top 10](https://owasp.org/www-project-top-ten/) · [JWT Best Practices (RFC 8725)](https://tools.ietf.org/html/rfc8725) · [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
**Relacionado**: [ARCHITECTURE.md](./ARCHITECTURE.md) · [API.md](./API.md)
