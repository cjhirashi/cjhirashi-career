# Plantillas PDF — `/pdf-templates`

Plantillas HTML/CSS para generación de CVs, cover letters y otros documentos PDF.

**Prefijo:** `/pdf-templates`  
**Tag OpenAPI:** `PDF Templates`  
**Auth:** JWT requerido

## Arquitectura

```mermaid
flowchart TB
    Admin[Admin Panel] --> Tpl[routes/pdf_templates.py]
    Admin --> Styles[routes/pdf_template_styles.py]
    Tpl --> Render[pdf_template_render]
    Tpl --> CSS[pdf_template_css]
    Tpl --> PDF[pdf_service]
    PDF --> Gen[pdf_generator WeasyPrint]
    Tpl --> Repo[CareerRepository]
    Styles --> Repo
    Repo --> Models[PdfOutputTemplate / PdfTemplateStyle]
    Models --> PG[(PostgreSQL)]
    Agent[agente pdf_design] --> Tpl
```

---

## Archivos fuente

| Capa | Archivo |
|------|---------|
| Rutas | `src/routes/pdf_templates.py` |
| Schemas | `src/schemas/pdf_template.py` |
| Modelo | `src/models/pdf_output_template.py` |
| Render | `src/services/pdf_template_render.py` |
| PDF | `src/services/pdf_service.py` |

Usa `CareerRepository` con `resource_key="pdf-output-templates"` y **`vectorize=False`**.

---

## Endpoints

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/pdf-templates` | Listar plantillas (`?document_type=cv`) |
| `GET` | `/pdf-templates/defaults/by-type` | Plantilla default por tipo |
| `GET` | `/pdf-templates/{template_id}` | Obtener una (`pdt-N`) |
| `POST` | `/pdf-templates` | Crear plantilla |
| `PUT` | `/pdf-templates/{template_id}` | Actualizar (incrementa `version`) |
| `DELETE` | `/pdf-templates/{template_id}` | Eliminar |
| `POST` | `/pdf-templates/{template_id}/render` | Renderizar PDF desde HTML |

---

## POST /pdf-templates — Crear

```json
{
  "slug": "cv-moderno",
  "document_type": "cv",
  "title": "CV Moderno",
  "html_template": "<html>...{{name}}...</html>",
  "css_content": "body { font-family: sans-serif; }",
  "is_default": false
}
```

**201** → `PdfOutputTemplateResponse` con `id: "pdt-1"`

---

## POST /pdf-templates/{id}/render

```json
{
  "variables": {
    "name": "Carlos Jiménez",
    "title": "Arquitecto de Soluciones",
    "skills": ["Python", "AWS"]
  },
  "title": "CV - Carlos Jiménez"
}
```

**Respuesta:** stream PDF (`application/pdf`)

**Flujo:**
1. Carga plantilla del usuario
2. `render_template_html()` — sustituye variables Jinja-like
3. `generate_html_template_pdf()` — WeasyPrint/wkhtmltopdf según config

---

## Tipos de documento

| `document_type` | Uso |
|-----------------|-----|
| `cv` | Curricula |
| `cover_letter` | Cartas de presentación |
| `other` | Documentos custom |

---

## Integraciones

| Consumidor | Cómo usa plantillas |
|------------|---------------------|
| Admin Panel | UI CRUD de plantillas + preview |
| `POST /career/cv-versions/{id}/pdf` | PDF de CV desde markdown + template |
| Agent Bedrock | Tools `list/get/create/update_pdf_template`, `generate_pdf` |
| Perfil `pdf_design` | Especialista en diseño de plantillas |

---

## Ejemplo

```bash
# Listar plantillas CV
curl -s "http://localhost:8001/pdf-templates?document_type=cv" \
  -H "Authorization: Bearer $TOKEN"

# Renderizar
curl -s -X POST http://localhost:8001/pdf-templates/pdt-1/render \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"variables":{"name":"Carlos"},"title":"Mi CV"}' \
  -o output.pdf
```

Ver también: [career-search](../career-search/README.md), [bedrock](../bedrock/README.md)
