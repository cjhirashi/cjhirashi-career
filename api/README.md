# MCP Tools API

API REST con autenticación JWT y gestión de documentos en PostgreSQL para el ecosistema MCP Tools Server.

## Características

- **Autenticación JWT** con bcrypt para hashing de passwords
- **PostgreSQL** como base de datos con SQLAlchemy async
- **FastAPI** con validación Pydantic
- **CORS** configurado para integración con frontend
- **CRUD completo** de documentos con aislamiento por usuario
- **Health checks** y logging robusto
- **Docker** ready con Dockerfile optimizado

## Stack Tecnológico

- **Framework**: FastAPI 0.109.0
- **ORM**: SQLAlchemy 2.0.25 (async)
- **Base de Datos**: PostgreSQL con asyncpg
- **Autenticación**: JWT (pyjwt) + bcrypt
- **Validación**: Pydantic v2
- **Server**: Uvicorn

## Estructura del Proyecto

```
api/
├── Dockerfile                # Imagen Docker
├── requirements.txt          # Dependencias Python
├── .env.example             # Ejemplo de variables de entorno
├── init.sql                 # Script de inicialización de BD
├── app.py                   # Punto de entrada FastAPI
├── config.py                # Configuración y settings
├── database.py              # Conexión y sesiones de BD
├── models/                  # Modelos SQLAlchemy
│   ├── user.py             # Modelo User
│   └── document.py         # Modelo Document
├── schemas/                 # Schemas Pydantic
│   ├── user.py             # Schemas de usuario y auth
│   └── document.py         # Schemas de documento
├── routes/                  # Endpoints de la API
│   ├── auth.py             # Login, logout, registro
│   └── documents.py        # CRUD de documentos
├── middleware/              # Middleware personalizado
│   └── auth.py             # Validación JWT
└── utils/                   # Utilidades
    ├── security.py         # Hashing y JWT
    └── constants.py        # Constantes globales
```

## Instalación

### Opción 1: Docker (Recomendado)

```bash
# Construir imagen
docker build -t mcp-api:latest .

# Ejecutar con docker-compose (ver docker-compose.yml del proyecto raíz)
docker compose up -d mcp-api
```

### Opción 2: Local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Inicializar base de datos (ejecutar init.sql en PostgreSQL)
psql -U user -d mcp_db -f init.sql

# Ejecutar servidor
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

## Configuración

### Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/mcp_db
SECRET_KEY=tu-clave-secreta-muy-segura-min-32-caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:8003,http://mcp_frontend:8000
DEBUG=false
```

### Base de Datos

El script `init.sql` crea:
- Tabla `users` con índices
- Tabla `documents` con índices y JSONB
- Trigger para `updated_at` automático
- Usuario de prueba: `usuario` / `password123`
- Documentos de ejemplo

## API Endpoints

### Autenticación

#### POST /auth/login
Login con username y password.

**Request:**
```json
{
  "username": "usuario",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": 1,
    "username": "usuario",
    "email": "usuario@example.com",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

#### POST /auth/logout
Logout (cliente elimina token).

**Response:**
```json
{
  "message": "Logout exitoso. Elimina el token del cliente."
}
```

#### POST /auth/register
Registro de nuevo usuario.

**Request:**
```json
{
  "username": "nuevousuario",
  "email": "nuevo@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "id": 2,
  "username": "nuevousuario",
  "email": "nuevo@example.com",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Documentos (Requieren Autenticación)

Todos los endpoints de documentos requieren el header:
```
Authorization: Bearer <tu_token_jwt>
```

#### GET /documents
Lista documentos del usuario con paginación.

**Query Params:**
- `skip`: Offset (default: 0)
- `limit`: Límite (default: 100, max: 500)

**Response:**
```json
{
  "total": 2,
  "documents": [
    {
      "id": 1,
      "user_id": 1,
      "type": "cv",
      "title": "CV Ejemplo",
      "data": {...},
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### GET /documents/{id}
Obtiene un documento específico.

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "type": "cv",
  "title": "CV Ejemplo",
  "data": {...},
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

#### POST /documents
Crea un nuevo documento.

**Request:**
```json
{
  "type": "cv",
  "title": "Mi CV",
  "data": {
    "nombre": "John Doe",
    "email": "john@example.com",
    ...
  }
}
```

**Response:** Documento creado (201)

#### PUT /documents/{id}
Actualiza un documento.

**Request:**
```json
{
  "title": "CV Actualizado",
  "data": {...}
}
```

**Response:** Documento actualizado

#### DELETE /documents/{id}
Elimina un documento.

**Response:** 204 No Content

#### GET /documents/type/{type}
Lista documentos por tipo.

**Query Params:**
- `skip`: Offset (default: 0)
- `limit`: Límite (default: 100)

**Response:**
```json
{
  "total": 1,
  "documents": [...]
}
```

### Health Check

#### GET /health
Estado de la API.

**Response:**
```json
{
  "status": "healthy",
  "app_name": "MCP Tools API",
  "version": "1.0.0"
}
```

## Autenticación JWT

### Flujo de Autenticación

1. **Login**: POST a `/auth/login` con username/password
2. **Recibir token**: La API retorna `access_token`
3. **Usar token**: Incluir en header `Authorization: Bearer <token>` en requests subsecuentes
4. **Expiración**: El token expira en 7 días (configurable)
5. **Logout**: Eliminar token del cliente

### Ejemplo con curl

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"usuario","password":"password123"}' \
  | jq -r '.access_token')

# Usar token para listar documentos
curl http://localhost:8001/documents \
  -H "Authorization: Bearer $TOKEN"
```

## Seguridad

- **Passwords**: Hasheados con bcrypt (cost factor 12)
- **JWT**: Firmado con HS256, expira en 7 días
- **CORS**: Configurado para orígenes específicos
- **SQL Injection**: Protegido por SQLAlchemy ORM
- **XSS**: Validación de entrada con Pydantic
- **Usuario no-root**: Dockerfile usa usuario `apiuser`

## Testing

### Test Manual con cURL

```bash
# Health check
curl http://localhost:8001/health

# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"usuario","password":"password123"}'

# Crear documento (usa el token del login)
curl -X POST http://localhost:8001/documents \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "cv",
    "title": "Mi CV",
    "data": {"nombre": "Test"}
  }'

# Listar documentos
curl http://localhost:8001/documents \
  -H "Authorization: Bearer <TOKEN>"
```

### Test con Thunder Client / Postman

1. Importar endpoints desde Swagger UI: `http://localhost:8001/docs`
2. Hacer login y copiar `access_token`
3. Configurar Collection con Bearer Token
4. Probar endpoints

## Logging

La API registra logs en stdout con formato:

```
2024-01-15 10:00:00 - app - INFO - MCP Tools API v1.0.0 initialized
2024-01-15 10:05:00 - routes.auth - INFO - User logged in: usuario
2024-01-15 10:10:00 - routes.documents - INFO - Document created: id=1, type=cv, user=usuario
```

Ver logs con Docker:

```bash
docker logs mcp_api -f
```

## Errores Comunes

### 401 Unauthorized
- Token inválido o expirado
- Token no incluido en header
- Solución: Hacer login nuevamente

### 404 Not Found
- Documento no existe o no pertenece al usuario
- Solución: Verificar ID y permisos

### 422 Validation Error
- Datos de entrada inválidos
- Solución: Revisar schema en `/docs`

### 500 Internal Server Error
- Error en base de datos o servidor
- Solución: Revisar logs

## Despliegue

### Docker Compose

Agregar al `docker-compose.yml` del proyecto raíz:

```yaml
services:
  mcp-api:
    build:
      context: ./api
      dockerfile: Dockerfile
    container_name: mcp_api
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/mcp_db
      - SECRET_KEY=${SECRET_KEY}
    networks:
      - network-cjhirashi-srv
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: mcp_postgres
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=mcp_db
    volumes:
      - ./api/init.sql:/docker-entrypoint-initdb.d/init.sql
      - postgres_data:/var/lib/postgresql/data
    networks:
      - network-cjhirashi-srv
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  network-cjhirashi-srv:
    external: true
```

### Producción

1. **Cambiar SECRET_KEY**: Generar clave aleatoria segura
2. **Configurar HTTPS**: Usar reverse proxy (Caddy, Nginx)
3. **Database**: PostgreSQL con backups automáticos
4. **Monitoring**: Logs centralizados, health checks
5. **Rate limiting**: Implementar con middleware
6. **Secrets**: Usar gestor de secretos (Vault, AWS Secrets)

## Documentación Interactiva

Una vez ejecutando, accede a:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Mantenimiento

### Migrations

Para cambios en el schema de BD, usar Alembic:

```bash
pip install alembic
alembic init alembic
# Configurar alembic.ini y env.py
alembic revision --autogenerate -m "Descripción del cambio"
alembic upgrade head
```

### Backups

Backup de PostgreSQL:

```bash
docker exec mcp_postgres pg_dump -U user mcp_db > backup.sql
```

Restaurar:

```bash
docker exec -i mcp_postgres psql -U user mcp_db < backup.sql
```

## Contribuir

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/nueva-feature`
3. Commit: `git commit -m 'feat: Agregar nueva feature'`
4. Push: `git push origin feature/nueva-feature`
5. Crear Pull Request

## Licencia

Proyecto interno del ecosistema cjhirashi.

## Soporte

- Email: cjhirashi@gmail.com
- Docs: `/docs/` en el proyecto raíz

---

**Última actualización**: 2024-01-15  
**Versión**: 1.0.0
