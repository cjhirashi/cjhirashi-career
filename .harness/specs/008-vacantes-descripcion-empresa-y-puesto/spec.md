---
titulo: "Vacantes: quiénes son, qué buscan, qué ofrecen y cultura laboral"
tipo: spec
estado: approved
fecha: 2026-10-13
feature_id: "008"
anchor_mode: advisory
anchor_commit: null
covers:
  - .harness/specs/008-vacantes-descripcion-empresa-y-puesto/**
  - cjhirashi-career-api/src/models/vacancy.py
  - cjhirashi-career-api/src/schemas/career_search.py
  - cjhirashi-career-api/src/repositories/career_repository.py
  - cjhirashi-career-api/alembic/versions/d8f2b5a13c97_vacancy_descriptive_texts.py
  - cjhirashi-career-api/tests/unit/test_vacancy_descriptive_texts.py
  - cjhirashi-career-api/tests/unit/test_vacancy_descriptive_texts_migration.py
  - cjhirashi-career-api/docs/sections/career-search/README.md
  - cjhirashi-career-admin/src/types/career.ts
  - cjhirashi-career-admin/src/config/careerResources.ts
  - cjhirashi-career-admin/src/tests/config/vacanciesConfig.test.ts
  - cjhirashi-career-admin/src/tests/components/career/VacancyDescriptiveTexts.test.tsx
---

# Vacantes: quiénes son, qué buscan, qué ofrecen y cultura laboral

## 1 · Contexto del dominio

**Problema:** al revisar una vacante, la información cualitativa de la publicación (quién
es la empresa, qué perfil busca, qué ofrece y cómo es su cultura) no tiene dónde vivir.
Hoy acaba mezclada en `analysis_notes`/`notes` o se pierde, y el agente no la puede usar
al adaptar el CV o la carta. El consumidor principal es un **agente externo** que lee la
base a través de la API REST (`/career/vacancies`). El harness de agentes (Bedrock) y la
indexación salen de la API en la spec 009; 008 no depende de ella.

Hoy `vacancies` tiene datos estructurados (`required_skills`, `years_experience_required`,
`salary_min/max`, `work_modality`…) pero ningún texto descriptivo por apartado.
`target_companies.company_culture` (spec 006) describe la cultura **a nivel empresa** y
sólo existe cuando la vacante está enlazada a una empresa diana.

Dependencias: API (`models/vacancy.py`, `schemas/career_search.py`), Alembic, exclusión
transitoria de la KB (`_KB_EXCLUDED_COLUMNS` en `career_repository.py`, D-05), Admin (`careerResources.ts`, `types/career.ts`). Sin impacto en
`cjhirashi-career-ai` ni en el Portfolio.

## 2 · Alcance

### En alcance
- Cuatro atributos nuevos de **texto largo libre** en `vacancies`, propios de la vacante.
- CRUD REST de vacantes: aceptarlos en Create/Update y devolverlos en Response.
- Exclusión **transitoria** del texto indexado en la KB mientras exista (D-05).
- Admin: cuatro áreas de texto en el formulario y en la ficha de detalle, contiguas y en
  un orden fijo. **No** como columnas de la tabla.
- Migración reversible.

### Fuera de alcance
- Sincronizar o heredar datos de `target_companies` (ni `company_culture` ni otros), ni
  precargar al enlazar una empresa diana (D-02).
- Rellenarlos automáticamente desde *job discovery* / importar por URL (hoy sólo se
  guarda un *snippet*; extraer apartados exige LLM → feature aparte).
- Un modo de presentación propio para estos campos en el Admin: la ficha usa el
  renderizado vigente de áreas de texto (Markdown, D-06).
- Reindex de la KB: no aplica (los campos no se indexan y las vacantes existentes no cambian).
- Desactivar o cambiar el indexado de otras columnas o tablas.
- Tocar `required_skills`, `analysis_notes`, `notes` u otros campos existentes.

## 3 · Modelo de datos y contratos de E/S

| Campo | Etiqueta (Admin) | Tipo | Nulabilidad | Escritura |
|---|---|---|---|---|
| `company_overview` | Quiénes son | text | NULL | Create / Update |
| `candidate_profile` | Qué buscan | text | NULL | Create / Update |
| `offer_summary` | Qué ofrecen | text | NULL | Create / Update |
| `work_culture` | Cultura laboral | text | NULL | Create / Update |

Orden canónico (formulario y ficha): Quiénes son → Qué buscan → Qué
ofrecen → Cultura laboral.

Normalización en la API: se recortan espacios al inicio y al final; una cadena vacía o
sólo espacios se guarda como `NULL`. Longitud máxima **10 000 caracteres** por campo
(D-04).

Fronteras:
- **REST `/career/vacancies`** (CRUD genérico): Create/Update aceptan los cuatro campos
  (opcionales); Response los devuelve siempre (valor o `null`). Excederse de longitud →
  422 con el formato de validación vigente (`{"detail", "errors"}`; 007 D-14).
- **Tools Bedrock `create/update_career_record`**: escriben por el repositorio sin pasar
  por el schema, así que **no** aplican trim/vacío→`NULL` ni el tope de longitud; RF-004 y
  RF-005 rigen para REST (D-07). Con la spec 009 el harness escribirá vía REST y heredará
  el contrato.
- **KB** (transitorio, hasta la spec 009): los cuatro campos **no** entran al texto
  indexado de la vacante (D-05).
- **BD `vacancies`**: cuatro columnas `text` nullable, sin default.

## 4 · Criterios de aceptación (EARS)

- **RF-001** CUANDO se crea o actualiza una vacante con cualquiera de los cuatro campos,
  el sistema DEBE persistirlo y devolverlo en la respuesta.
- **RF-002** El sistema DEBE devolver los cuatro campos en toda respuesta de vacante,
  con `null` cuando no tengan valor.
- **RF-003** CUANDO un Update omite alguno de los campos, el sistema NO DEBE alterar su
  valor almacenado.
- **RF-004** CUANDO un campo llega vacío o sólo con espacios, el sistema DEBE guardarlo
  como `NULL`; CUANDO trae espacios al inicio o al final, DEBE guardarlo recortado.
- **RF-005** SI un campo supera 10 000 caracteres, ENTONCES el sistema DEBE responder
  422 sin persistir el cambio.
- **RF-006** *(transitorio; se retira con la spec 009)* MIENTRAS la API indexe vacantes
  en la KB, CUANDO se indexa una vacante, el texto NO DEBE incluir ninguno de los cuatro
  campos, aunque tengan valor.
- **RF-007** La migración DEBE añadir las cuatro columnas nullable sin alterar las filas
  existentes, y DEBE poder bajar eliminándolas.
- **RF-008** El formulario de Vacante del Admin DEBE ofrecer los cuatro campos como áreas
  de texto de ancho completo, contiguas, en el orden canónico y con las etiquetas de §3.
- **RF-009** La ficha de detalle de Vacante del Admin DEBE mostrar los cuatro campos en
  el orden canónico con el renderizado vigente de áreas de texto (Markdown), como el resto
  de campos de texto largo de la ficha.
- **RF-010** La tabla de Vacantes del Admin NO DEBE añadir columnas para estos campos.

## 5 · Casos límite y errores

- `null` explícito en Update → borra el valor (a diferencia de omitirlo, RF-003).
- Texto con saltos de línea, viñetas pegadas o emojis → se guarda tal cual (sólo trim).
- Exactamente 10 000 caracteres → válido; 10 001 → 422.
- La vacante sin empresa diana enlazada funciona igual (los campos no dependen de ella).

## 6 · Registro de decisiones y descartes

- **D-01 (usuario, 2026-10-13, Fase 1):** texto largo libre por atributo. *Descartado:*
  listas de puntos JSONB (rígidas para párrafos).
- **D-02 (usuario, 2026-10-13, Fase 1):** los cuatro son propios de la vacante, tal como
  los describe la publicación; no se sincronizan con `target_companies`. *Descartado:*
  precargar desde la empresa diana; heredar "quiénes son"/"cultura" de la empresa (las
  vacantes sin empresa diana se quedarían sin datos).
- **D-03 (usuario, 2026-10-13, Fase 1):** en el Admin, formulario y ficha; no columnas
  de tabla. *Descartado:* columnas opcionales truncadas.
- **D-04 (usuario, 2026-10-13, Gate 1 — confirmada):** nombres de columna `company_overview`,
  `candidate_profile`, `offer_summary`, `work_culture`; límite 10 000 caracteres por
  campo (protege la API, el Admin y al agente externo de pegados accidentales enormes);
  trim + vacío → `NULL`.
- **D-05 (usuario, 2026-10-13, Gate 1):** 008 se cierra **sin parte de KB propia**; la
  indexación sale de la API en la spec 009 (harness de agentes a `cjhirashi-career-ai`).
  Como el indexado se dispara en cada escritura y 008 puede desplegarse antes que 009,
  los cuatro campos se añaden a `_KB_EXCLUDED_COLUMNS` como exclusión **transitoria**
  (una línea, como 007 D-13) para no generar embeddings sin consumidor; 009 la retira
  junto con el resto del indexado. *Descartado:* indexarlos (coste sin consumidor);
  pausar 008 hasta terminar 009 (bloquea una feature pequeña e independiente).
- **D-06 (usuario, 2026-10-13, Fase 2 — enmienda RF-009):** la ficha muestra los cuatro
  campos con el renderizado Markdown vigente de las áreas de texto. Un salto de línea
  simple se colapsa; los párrafos se separan con línea en blanco. *Descartado:* una opción
  nueva `plainText` en la configuración del Admin (extensión que no compensa).
- **D-07 (usuario, 2026-10-13, Fase 2):** la normalización (RF-004) y el tope (RF-005)
  rigen sólo para la API REST; las tools Bedrock internas no se adaptan porque la spec
  009 las mueve a `cjhirashi-career-ai` y escribirán vía REST. *Descartado:* normalizar
  también en el repositorio (código que 009 deja sin uso).

## 7 · Requisitos no funcionales

- **RNF-001:** cobertura ≥ 80 % por módulo tocado; tests trazados con
  `@pytest.mark.requisito` / `describe("RF-0NN")`.
- **RNF-002:** ninguna prueba llama a Bedrock ni a Qdrant reales.
- **RNF-003:** despliegue con backup previo, migración y verificación en vivo (crear,
  actualizar, limpiar y consultar una vacante con los cuatro campos).

## 8 · UX (Admin)

Detalle de UX (etiquetas, `helpText`, alto de las áreas de texto, posición en el
formulario) → lo aporta `experto-ux-ui` en la Fase 2.
