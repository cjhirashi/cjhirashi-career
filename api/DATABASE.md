# Database Schema - MCP Tools API

Documentación del esquema de base de datos PostgreSQL.

## Overview

La base de datos `mcp_db` almacena usuarios y sus documentos en formato JSON. Usa PostgreSQL 15 con soporte para JSONB, índices y triggers.

## Diagrama de Relaciones

```
┌─────────────────────────┐
│        users            │
├─────────────────────────┤
│ id (PK)                 │ ◄──┐
│ username (UNIQUE)       │    │
│ email (UNIQUE)          │    │
│ password_hash           │    │
│ created_at              │    │
└─────────────────────────┘    │
                               │
                               │ 1:N
                               │
┌─────────────────────────┐    │
│      documents          │    │
├─────────────────────────┤    │
│ id (PK)                 │    │
│ user_id (FK) ───────────────┘
│ type                    │
│ title                   │
│ data (JSONB)            │
│ created_at              │
│ updated_at              │
└─────────────────────────┘
```

## Tabla: users

Almacena información de autenticación y perfil de usuarios.

### Columnas

| Columna       | Tipo          | Restricciones        | Descripción                              |
|---------------|---------------|----------------------|------------------------------------------|
| id            | SERIAL        | PRIMARY KEY          | Identificador único autoincrementable    |
| username      | VARCHAR(255)  | UNIQUE, NOT NULL     | Nombre de usuario único                  |
| email         | VARCHAR(255)  | UNIQUE, NOT NULL     | Email único del usuario                  |
| password_hash | VARCHAR(255)  | NOT NULL             | Hash bcrypt de la contraseña             |
| created_at    | TIMESTAMP     | DEFAULT CURRENT_TS   | Fecha de creación del usuario            |

### Índices

- `idx_users_username`: Índice en `username` para búsquedas rápidas
- `idx_users_email`: Índice en `email` para validación de unicidad

### SQL

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

### Ejemplo de Registro

```json
{
  "id": 1,
  "username": "usuario",
  "email": "usuario@example.com",
  "password_hash": "$2b$12$KIX7Zh3v5QXMhXY5nZj5VOZLmqP8h6u1yWJZ5sJZwLqxN5vYqJWLq",
  "created_at": "2024-01-15T10:00:00Z"
}
```

## Tabla: documents

Almacena documentos (CVs, cover letters, etc.) con datos en formato JSON.

### Columnas

| Columna    | Tipo          | Restricciones                    | Descripción                              |
|------------|---------------|----------------------------------|------------------------------------------|
| id         | SERIAL        | PRIMARY KEY                      | Identificador único autoincrementable    |
| user_id    | INTEGER       | FK → users(id), NOT NULL         | ID del usuario propietario               |
| type       | VARCHAR(50)   | NOT NULL                         | Tipo de documento (cv, cover_letter)     |
| title      | VARCHAR(255)  | NULL                             | Título descriptivo del documento         |
| data       | JSONB         | NOT NULL                         | Contenido del documento en JSON          |
| created_at | TIMESTAMP     | DEFAULT CURRENT_TS               | Fecha de creación del documento          |
| updated_at | TIMESTAMP     | DEFAULT CURRENT_TS, AUTO-UPDATE  | Fecha de última actualización            |

### Índices

- `idx_documents_user_id`: Índice en `user_id` para consultas por usuario
- `idx_documents_type`: Índice en `type` para filtrado por tipo

### Foreign Keys

- `user_id` → `users(id)` con `ON DELETE CASCADE`
  - Si se elimina un usuario, se eliminan todos sus documentos

### Triggers

- `update_documents_updated_at`: Actualiza automáticamente `updated_at` en cada UPDATE

### SQL

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_type ON documents(type);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Ejemplo de Registro

```json
{
  "id": 1,
  "user_id": 1,
  "type": "cv",
  "title": "CV Profesional",
  "data": {
    "nombre": "Juan Pérez",
    "email": "juan@example.com",
    "telefono": "+34 600 123 456",
    "titulo_profesional": "Desarrollador Full Stack",
    "experiencia": [
      {
        "empresa": "Tech Corp",
        "puesto": "Senior Developer",
        "años": "2020-2024"
      }
    ],
    "habilidades": ["Python", "FastAPI", "React"]
  },
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T12:30:00Z"
}
```

## Tipos de Documentos

### type: "cv"

Estructura de datos recomendada para CVs:

```json
{
  "nombre": "string",
  "email": "string",
  "telefono": "string",
  "titulo_profesional": "string",
  "resumen": "string",
  "experiencia": [
    {
      "empresa": "string",
      "puesto": "string",
      "años": "string",
      "descripcion": "string"
    }
  ],
  "educacion": [
    {
      "institucion": "string",
      "titulo": "string",
      "años": "string"
    }
  ],
  "habilidades": ["string"],
  "idiomas": ["string"],
  "certificaciones": ["string"]
}
```

### type: "cover_letter"

Estructura de datos recomendada para cover letters:

```json
{
  "nombre": "string",
  "email": "string",
  "empresa": "string",
  "puesto": "string",
  "fecha": "string",
  "contenido": "string"
}
```

## Consultas Comunes

### Obtener todos los documentos de un usuario

```sql
SELECT * FROM documents
WHERE user_id = 1
ORDER BY created_at DESC;
```

### Obtener documentos por tipo

```sql
SELECT * FROM documents
WHERE user_id = 1 AND type = 'cv'
ORDER BY created_at DESC;
```

### Buscar en datos JSON

```sql
-- Buscar documentos donde el nombre contenga "Juan"
SELECT * FROM documents
WHERE user_id = 1
  AND data->>'nombre' LIKE '%Juan%';

-- Buscar documentos con habilidad específica
SELECT * FROM documents
WHERE user_id = 1
  AND data->'habilidades' ? 'Python';
```

### Actualizar campo específico en JSON

```sql
-- Actualizar solo el email en el JSON data
UPDATE documents
SET data = jsonb_set(data, '{email}', '"nuevo@example.com"')
WHERE id = 1;
```

## Migraciones

### Agregar nueva columna

```sql
ALTER TABLE documents
ADD COLUMN is_public BOOLEAN DEFAULT false;
```

### Crear índice en campo JSON

```sql
-- Índice GIN para búsquedas en JSONB
CREATE INDEX idx_documents_data_gin ON documents USING GIN (data);

-- Índice en campo específico del JSON
CREATE INDEX idx_documents_nombre ON documents ((data->>'nombre'));
```

## Backups

### Backup completo

```bash
# Backup de toda la base de datos
docker exec mcp_postgres pg_dump -U mcpuser mcp_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup solo de datos (sin schema)
docker exec mcp_postgres pg_dump -U mcpuser --data-only mcp_db > data_backup.sql
```

### Restaurar desde backup

```bash
# Restaurar backup completo
docker exec -i mcp_postgres psql -U mcpuser mcp_db < backup_20240115_100000.sql

# Restaurar solo datos
docker exec -i mcp_postgres psql -U mcpuser mcp_db < data_backup.sql
```

## Mantenimiento

### Analizar y optimizar

```sql
-- Analizar estadísticas de las tablas
ANALYZE users;
ANALYZE documents;

-- Vacuuming para liberar espacio
VACUUM ANALYZE users;
VACUUM ANALYZE documents;
```

### Estadísticas de uso

```sql
-- Total de usuarios
SELECT COUNT(*) FROM users;

-- Total de documentos por tipo
SELECT type, COUNT(*) as total
FROM documents
GROUP BY type
ORDER BY total DESC;

-- Documentos por usuario
SELECT u.username, COUNT(d.id) as document_count
FROM users u
LEFT JOIN documents d ON u.id = d.user_id
GROUP BY u.id, u.username
ORDER BY document_count DESC;
```

## Seguridad

### Permisos

```sql
-- Crear usuario de solo lectura
CREATE USER readonly_user WITH PASSWORD 'readonly_pass';
GRANT CONNECT ON DATABASE mcp_db TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- Revocar permisos de escritura
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM readonly_user;
```

### Auditoría

Para tracking de cambios, considerar agregar tabla de auditoría:

```sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    changes JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Limitaciones

- **Max JSON size**: PostgreSQL no tiene límite estricto para JSONB, pero se recomienda < 1MB por documento
- **Índices GIN**: Consumen más espacio que índices B-tree
- **Búsquedas full-text**: Para búsquedas complejas en texto, considerar pg_trgm o integración con Elasticsearch

## Referencias

- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/15/datatype-json.html)
- [PostgreSQL Triggers](https://www.postgresql.org/docs/15/plpgsql-trigger.html)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

---

**Última actualización**: 2024-01-15
