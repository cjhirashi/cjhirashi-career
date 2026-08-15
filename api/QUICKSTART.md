# Quick Start Guide - MCP Tools API

Guía rápida para poner en marcha la API en 5 minutos.

## 1. Iniciar los Servicios

Desde el directorio raíz del proyecto:

```bash
# Construir e iniciar todos los servicios (incluye PostgreSQL y API)
docker compose up -d postgres mcp-api

# Ver logs en tiempo real
docker logs mcp_api -f
```

## 2. Verificar que la API está Running

```bash
# Health check
curl http://localhost:8001/health

# Debería retornar: {"status":"healthy","app_name":"MCP Tools API","version":"1.0.0"}
```

## 3. Hacer Login

```bash
# Login con usuario de prueba
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"usuario","password":"password123"}' | jq

# Guardar token en variable (Linux/Mac)
export TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"usuario","password":"password123"}' | jq -r '.access_token')

echo $TOKEN
```

## 4. Listar Documentos

```bash
# Listar todos los documentos del usuario
curl http://localhost:8001/documents \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 5. Crear Documento

```bash
# Crear un nuevo CV
curl -X POST http://localhost:8001/documents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "cv",
    "title": "Mi CV Profesional",
    "data": {
      "nombre": "Juan Pérez",
      "email": "juan.perez@example.com",
      "telefono": "+34 600 123 456",
      "titulo_profesional": "Desarrollador Full Stack",
      "resumen": "Desarrollador con 5 años de experiencia",
      "experiencia": [
        {
          "empresa": "Tech Corp",
          "puesto": "Senior Developer",
          "años": "2020-2024",
          "descripcion": "Desarrollo de aplicaciones web con Python y React"
        }
      ],
      "educacion": [
        {
          "institucion": "Universidad Politécnica",
          "titulo": "Ingeniería Informática",
          "años": "2015-2019"
        }
      ],
      "habilidades": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"]
    }
  }' | jq
```

## 6. Obtener Documento por ID

```bash
# Guardar el ID del documento creado
DOC_ID=1

# Obtener documento
curl http://localhost:8001/documents/$DOC_ID \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 7. Actualizar Documento

```bash
# Actualizar título y datos
curl -X PUT http://localhost:8001/documents/$DOC_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mi CV Actualizado",
    "data": {
      "nombre": "Juan Pérez García",
      "email": "juan.perez@example.com"
    }
  }' | jq
```

## 8. Listar por Tipo

```bash
# Listar solo CVs
curl http://localhost:8001/documents/type/cv \
  -H "Authorization: Bearer $TOKEN" | jq

# Listar solo cover letters
curl http://localhost:8001/documents/type/cover_letter \
  -H "Authorization: Bearer $TOKEN" | jq
```

## 9. Eliminar Documento

```bash
# Eliminar documento (retorna 204 No Content)
curl -X DELETE http://localhost:8001/documents/$DOC_ID \
  -H "Authorization: Bearer $TOKEN" -v
```

## 10. Documentación Interactiva

Abre en tu navegador:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Ejecutar Tests Automáticos

### Test con Bash Script

```bash
cd api
./test_api.sh
```

### Test con Python

```bash
cd api
pip install httpx  # Si no está instalado
python test_integration.py
```

## Datos de Prueba

### Usuario por Defecto

- **Username**: `usuario`
- **Password**: `password123`
- **Email**: `usuario@example.com`

### Documentos de Ejemplo

El script `init.sql` crea automáticamente:
- 1 CV de ejemplo
- 1 Cover Letter de ejemplo

## Troubleshooting

### Error: Connection refused

```bash
# Verificar que los contenedores están corriendo
docker ps | grep mcp

# Ver logs de PostgreSQL
docker logs mcp_postgres

# Ver logs de la API
docker logs mcp_api
```

### Error: 401 Unauthorized

El token probablemente expiró (7 días). Hacer login de nuevo:

```bash
export TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"usuario","password":"password123"}' | jq -r '.access_token')
```

### Reiniciar Base de Datos

```bash
# Detener servicios
docker compose down

# Eliminar volumen de PostgreSQL (CUIDADO: borra todos los datos)
docker volume rm mcp-server_postgres_data

# Iniciar de nuevo (ejecuta init.sql automáticamente)
docker compose up -d postgres mcp-api
```

## Próximos Pasos

1. Explorar la [documentación completa](./README.md)
2. Revisar los [schemas de Pydantic](./schemas/)
3. Personalizar las [variables de entorno](./.env.example)
4. Integrar con el frontend React
5. Conectar con el servidor MCP Tools

## Recursos Adicionales

- **API Reference**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **Root Endpoint**: http://localhost:8001/

---

**Tip**: Usa `jq` para formatear el JSON en las respuestas de curl. Si no lo tienes instalado:

```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq
```
