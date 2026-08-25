"""Seed operational methodology «Plantillas PDF y estilos CSS» (section Diseño PDF).

Revision ID: f5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-08-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f5b6c7d8e9f0"
down_revision: Union[str, None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_METHODOLOGY_TITLE = "Plantillas PDF y estilos CSS"

_CONTENT = """\
# Plantillas PDF y estilos CSS

Metodología operativa del agente **agent_pdf_design** y del Admin Panel para CVs, cartas y documentos genéricos (WeasyPrint).

## Modelo de dos tablas

| Tabla | resource_key | ID | Responsabilidad |
|-------|--------------|-----|-----------------|
| `pdf_template_styles` | `pdf-template-styles` | `pds-N` | CSS reutilizable + guía de clases |
| `pdf_output_templates` | `pdf-output-templates` | `pdt-N` | HTML + referencia al estilo + variables |

## Relación

- **Un estilo → muchas plantillas** mediante `style_id` (FK en plantilla → `pds-N`).
- El CSS **nunca** va inline en la plantilla; siempre en el estilo referenciado.
- Al generar PDF: `html_template` con `{{variables}}` sustituidas + `css_content` del estilo enlazado.

## Flujo de trabajo

1. **Estilo primero:** `list_pdf_template_styles` o `create_pdf_template_style`.
2. Escribir `css_content` (WeasyPrint) y `style_guide` (Markdown: clases, etiquetas, para qué sirve cada una).
3. **Plantilla:** `create_pdf_template` con `html_template`, `style_id` y `variables` (Markdown: cada `{{nombre}}` y qué contenido lleva).
4. **Probar:** `generate_pdf` con variables de ejemplo.
5. Para reutilizar un estilo, leer `style_guide` con `get_pdf_template_style` antes de escribir HTML.

## Campos clave

### Estilo (`pds-N`)

- `slug`, `title`, `description`
- `css_content` — CSS completo
- `style_guide` — Markdown de clases/etiquetas disponibles
- `is_active`

### Plantilla (`pdt-N`)

- `slug`, `document_type` (`cv` | `cover-letter` | `generic`), `title`
- `html_template` — HTML con placeholders `{{variable}}`
- `style_id` — FK al estilo (`pds-N`)
- `variables` — Markdown documentando cada variable
- `is_default`, `is_active`

## Herramientas del agente

| Estilos | Plantillas | Render |
|---------|------------|--------|
| `list_pdf_template_styles` | `list_pdf_templates` | `generate_pdf` |
| `get_pdf_template_style` | `get_pdf_template` | |
| `create_pdf_template_style` | `create_pdf_template` | |
| `update_pdf_template_style` | `update_pdf_template` | |

Confirma campos con `describe_resource_schema` si hace falta.
"""


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO operational_methodologies (id, user_id, title, section, description, content)
            SELECT
                'opm-' || nextval('opm_id_seq'),
                u.id,
                :title,
                'Diseño PDF',
                'Separación de estilos CSS (pds-N) y plantillas HTML (pdt-N) con style_id FK.',
                :content
            FROM users u
            WHERE NOT EXISTS (
                SELECT 1 FROM operational_methodologies om
                WHERE om.user_id = u.id
                  AND om.section = 'Diseño PDF'
                  AND om.title = :title
            )
            """
        ),
        {"title": _METHODOLOGY_TITLE, "content": _CONTENT},
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM operational_methodologies WHERE section = 'Diseño PDF' AND title = :title"
        ).bindparams(title=_METHODOLOGY_TITLE)
    )
