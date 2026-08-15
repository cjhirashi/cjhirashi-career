# Guía de Inicio Rápido — MCP Tools Server

Bienvenido a **MCP Tools Server**, un servidor especializado en generar documentos profesionales en PDF (CVs y Cartas de Presentación) a través del **Model Context Protocol (MCP)**.

---

## Instalación y Setup

### Requisitos Previos

- **Docker** y **Docker Compose** (versiones recientes)
- **Git** para clonar el repositorio
- Acceso a `/mnt/disco2/cjhirashi-data/mcp-outputs` en el host (volumen persistente)

### 1. Clonar el Repositorio

```bash
git clone <repository-url> mcp-server
cd mcp-server
```

### 2. Verificar Estructura de Directorios

```bash
# El volumen persistente debe existir
mkdir -p /mnt/disco2/cjhirashi-data/mcp-outputs/cvs
mkdir -p /mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters
```

### 3. Levantar el Servidor

Desde la **raíz del proyecto**, ejecuta:

```bash
# Construir la imagen Docker
docker compose build --no-cache mcp-tools

# Iniciar el contenedor
docker compose up -d --force-recreate mcp-tools

# Verificar que está corriendo
docker logs mcp_tools_server --tail 20 -f
```

**Resultado esperado:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

El servidor estará disponible en: `http://<IP_SERVIDOR>:8002/sse`

---

## Uso Básico

### Herramienta 1: Generar CV en PDF

**Endpoint MCP:** `crear_cv_pdf`

```json
{
  "datos_cv_json": "{\"nombre\":\"Juan Pérez\",\"email\":\"juan@example.com\",\"titulo_profesional\":\"Senior Engineer\",\"experiencia\":[{\"empresa\":\"Acme Inc\",\"puesto\":\"Engineer\",\"años\":\"2020-2024\"}]}",
  "nombre_archivo": "cv_juan_perez.pdf"
}
```

**Respuesta:**
```
Éxito: PDF generado correctamente en '/mnt/disco2/cjhirashi-data/mcp-outputs/cvs/cv_juan_perez.pdf'
```

### Herramienta 2: Generar Carta de Presentación en PDF

**Endpoint MCP:** `crear_cover_letter_pdf`

```json
{
  "datos_cover_json": "{\"nombre\":\"Juan Pérez\",\"empresa\":\"Acme Inc\",\"puesto\":\"Senior Engineer\",\"cuerpo\":\"Estimado equipo...\"}",
  "nombre_archivo": "cover_juan_perez.pdf"
}
```

---

## Testing Local

Para probar localmente sin Docker:

```bash
cd server

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar tests
python test_cv.py
python test_cover.py
```

Los PDFs se generarán en el directorio de outputs configurado.

---

## Estructura de Datos: JSON del CV

El JSON del CV debe incluir estos campos (ejemplo):

```json
{
  "nombre": "Juan Pérez",
  "email": "juan@example.com",
  "telefono": "+34 600 123 456",
  "ubicacion": "Madrid, España",
  "titulo_profesional": "Senior Software Engineer",
  "resumen": "Ingeniero de software experimentado con...",
  "experiencia": [
    {
      "empresa": "Acme Inc",
      "puesto": "Senior Engineer",
      "años": "2020-2024",
      "descripcion": "Lideré el desarrollo del módulo X..."
    }
  ],
  "educacion": [
    {
      "institucion": "Universidad XYZ",
      "carrera": "Ingeniería Informática",
      "año": "2015"
    }
  ],
  "skills": ["Python", "JavaScript", "Docker", "Kubernetes"],
  "idiomas": [
    {
      "idioma": "Español",
      "nivel": "Nativo"
    },
    {
      "idioma": "Inglés",
      "nivel": "Fluido"
    }
  ]
}
```

Ver [templates en server/templates/cv_template.html](../../server/templates/cv_template.html) para la estructura completa esperada.

---

## Estructura de Datos: JSON de Cover Letter

```json
{
  "nombre": "Juan Pérez",
  "empresa": "Acme Inc",
  "puesto": "Senior Engineer",
  "fecha": "2026-08-15",
  "cuerpo": "Estimado equipo de reclutamiento...",
  "clausura": "Atentamente",
  "email": "juan@example.com"
}
```

Ver [templates en server/templates/cover_template.html](../../server/templates/cover_template.html) para detalles.

---

## Verificar Archivos Generados

Después de generar un CV o cover letter, verifica que los archivos se han creado correctamente:

```bash
# Ver CVs generados
ls -lah /mnt/disco2/cjhirashi-data/mcp-outputs/cvs/

# Ver cover letters generadas
ls -lah /mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters/
```

---

## Primeros Pasos — Documentación Recomendada

Una vez que tengas el servidor corriendo, consulta:

1. **[../README.md](../README.md)** — Descripción general del proyecto
2. **[../api/README.md](../api/README.md)** — Referencia completa de las herramientas MCP
3. **[../architecture/README.md](../architecture/README.md)** — Cómo funciona el sistema (diagramas)
4. **[../../server/README.md](../../server/README.md)** — Documentación técnica del servidor

---

## Solución de Problemas Comunes

### ¿El servidor no inicia?

```bash
# Ver logs en detalle
docker logs mcp_tools_server -f

# Verificar que el volumen está montado correctamente
docker inspect mcp_tools_server | grep -A 10 "Mounts"
```

### ¿El PDF no se genera?

1. Verifica que el JSON de entrada es válido: `python -m json.tool` en el JSON
2. Revisa los logs: `docker logs mcp_tools_server`
3. Asegúrate de que el directorio de output existe y tiene permisos de escritura

### ¿Puerto 8002 ya está en uso?

Cambia el puerto en `docker-compose.yml`:
```yaml
mcp-tools:
  ports:
    - "8004:8000"  # Usa 8004 en lugar de 8002
```

---

## Próximas Acciones

- [ ] Leer [../architecture/README.md](../architecture/README.md) para entender la arquitectura
- [ ] Revisar [../api/README.md](../api/README.md) para conocer todas las herramientas disponibles
- [ ] Configurar el frontend en `frontend/` si necesitas interfaz web
- [ ] Explorar personalizaciones de plantillas en `server/templates/`

---

**Última actualización:** 2026-08-15  
**Estado:** Documentación completa  
**Contacto:** Carlos (cjhirashi@gmail.com)
