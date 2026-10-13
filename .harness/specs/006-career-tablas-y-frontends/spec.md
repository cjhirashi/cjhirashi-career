---
titulo: "Career: tablas, relaciones y frontends del checklist de Paulina"
tipo: spec
estado: approved
fecha: 2026-10-09
feature_id: "006"
anchor_mode: advisory
anchor_commit: null
covers:
  - cjhirashi-career-api/src/models/identity.py
  - cjhirashi-career-api/src/models/certification.py
  - cjhirashi-career-api/src/models/role_gap_analysis.py
  - cjhirashi-career-api/src/models/target_company.py
  - cjhirashi-career-api/src/models/vacancy.py
  - cjhirashi-career-api/src/models/portal_about.py
  - cjhirashi-career-api/src/models/application.py
  - cjhirashi-career-api/src/models/application_interaction.py
  - cjhirashi-career-api/src/models/interview.py
  - cjhirashi-career-api/src/models/search_plan.py
  - cjhirashi-career-api/src/schemas/career_identity.py
  - cjhirashi-career-api/src/schemas/career_search.py
  - cjhirashi-career-api/src/schemas/career_digital.py
  - cjhirashi-career-api/src/schemas/public.py
  - cjhirashi-career-api/src/routes/career_common.py
  - cjhirashi-career-api/src/routes/public.py
  - cjhirashi-career-api/src/services/job_discovery/**
  - cjhirashi-career-api/alembic/versions/*_career_tables_checklist.py
  - cjhirashi-career-api/tests/unit/test_career_tables_checklist_migration.py
  - cjhirashi-career-api/tests/unit/test_career_tables_schemas.py
  - cjhirashi-career-api/tests/unit/test_career_crud_conflicts.py
  - cjhirashi-career-api/tests/unit/test_job_discovery.py
  - cjhirashi-career-api/tests/unit/test_public_routes.py
  - cjhirashi-career-admin/src/types/career.ts
  - cjhirashi-career-admin/src/config/careerResources.ts
  - cjhirashi-career-admin/src/tests/config/careerResources.test.ts
  - cjhirashi-career-admin/src/tests/pages/JobDiscoveryPage.test.tsx
  - cjhirashi-career-portfolio/src/types/index.ts
  - cjhirashi-career-portfolio/src/pages/AboutPage.tsx
  - cjhirashi-career-portfolio/src/tests/pages/AboutPage.spec.tsx
  - cjhirashi-career-portfolio/src/tests/fixtures/mockData.ts
  - docs/**
  - cjhirashi-career-api/src/models/README.md
  - cjhirashi-career-api/src/schemas/README.md
  - .harness/specs/006-career-tablas-y-frontends/**
---

# Career: tablas, relaciones y frontends del checklist de Paulina

## 1 · Contexto del dominio

Paulina inspeccionó los recursos de carrera en vivo y documentó trece puntos: cinco
fallos, una relación crítica, campos estructurados que hoy viven en texto libre y el
esquema no visible de tres tablas vacías. Carlos pidió aplicar el documento completo,
integrar los cambios en frontend, dejar el sistema funcionando y crear los commits.

El punto 1 (`operational-methodologies`) pertenece a la feature 005 ya iniciada: la BD
eliminó `section`/`subsection`/`notes`, pero el modelo desplegado aún las selecciona. La
feature 006 cubre los puntos 2–13 y depende del cierre coordinado de 005.

Diagnósticos en vivo de 2026-10-09:

- `search-plans` falla porque una fila contiene `completion_percentage=NULL` mientras
  el contrato de respuesta exige `int`.
- `company_boards` actualmente sí carga `Mutt Data / lever / muttdata` y devolvió tres
  vacantes para “Data Scientist”; se requiere prueba de regresión, no una reescritura.
- el CRUD genérico deja escapar el `IntegrityError` de `vacancy_url` como 500;
- `content-pieces` no existe y `publications.status` ya cubre borrador/programado/
  publicado;
- PostgreSQL no tiene las FK físicas de `applications.vacancy_id`,
  `application_interactions.application_id` ni `interviews.application_id`, aunque los
  modelos SQLAlchemy las declaran.

## 2 · Alcance

### En alcance

- Corregir los puntos 2–5 del checklist con causa raíz y contratos observables.
- Agregar `vacancies.target_company_id` y todos los campos de los puntos 7–12.
- Mantener `vacancies.company` como snapshot compatible; cuando se elige una empresa
  diana, el servicio valida propiedad por usuario y sincroniza el nombre en el write.
- Reparar las tres FK físicas detectadas como ausentes, sólo tras preflight sin
  huérfanos.
- Exponer todos los campos en modelos y esquemas Create/Update/Response.
- Integrar el panel Admin y el portal público About.
- Documentar el esquema real de applications/interactions/interviews.
- Migración reversible, pruebas por capa, respaldo y verificación en vivo.

### Fuera de alcance

- Crear un recurso o tabla `content-pieces` duplicado.
- Eliminar `vacancies.company` en esta versión.
- Convertir los campos de catálogo libre en enums PostgreSQL rígidos.
- Cambiar autenticación, modelos de agentes o proveedores de IA.
- Hacer push remoto sin una instrucción separada.

## 3 · Modelo de datos y contratos

Todos los campos nuevos son nullable para compatibilidad con filas existentes.

| Recurso | Campos nuevos | Tipo físico |
|---|---|---|
| `identity` | `modality_priority` | JSONB `list[str]` ordenada |
| | `availability_hours` | varchar(100) |
| `certifications` | `completion_date` | date |
| `role_gap_analysis` | `target_date` | date |
| `target_companies` | `industry_sector`, `funding_stage`, `hiring_velocity` | varchar |
| | `company_culture` | text |
| | `tech_stack` | JSONB `list[str]` |
| | `company_website`, `linkedin_company_url` | varchar(1024) |
| | `last_researched_at` | date |
| | `review_score` | numeric(3,2), 0..5 |
| `vacancies` | `target_company_id` | varchar(20), FK `target_companies.id`, SET NULL |
| | `location`, `work_modality`, `seniority_level` | varchar |
| | `salary_min`, `salary_max` | numeric(12,2), no negativos, min <= max |
| | `required_skills` | JSONB `list[str]` |
| | `years_experience_required` | integer >= 0 |
| | `posted_date` | date |
| | `application_status` | varchar(30) — *reemplazado por spec 007 (`process_stage` con catálogo cerrado + `vacancy_status` calculado, 007 D-02)* |
| | `priority` | varchar(10), P1/P2/P3 |
| | `contracting_model` | varchar(30), employee/contractor/freelance |
| | `contact_id` | varchar(20), FK `networking_contacts.id`, SET NULL |
| `portal_about` | `bio_text`, `headline` | text / varchar(255) |
| | `timeline_milestones` | JSONB `list[{period,title,description}]` |

Reglas de compatibilidad:

- `target_company_id` se backfillea sólo cuando existe una coincidencia única de
  `lower(trim(vacancies.company))` con `target_companies.company_name` para el mismo
  usuario; lo ambiguo queda NULL y se reporta.
- `vacancy_url` pasa de unique global a unique por `(user_id, vacancy_url)`.
- `portal_about.headline`/`bio_text` tienen prioridad pública; si son NULL, `/public/about`
  usa `identity.professional_tagline`/`bio_summary`.
- `completion_percentage` de search plans se backfillea a 0 y pasa a NOT NULL con
  default 0.
- los conflictos REST usan `application/problem+json` RFC 9457.

## 4 · Criterios de aceptación (EARS)

- **RF-001** CUANDO se lista `search-plans`, el sistema DEBE responder 200 aun cuando
  existan filas legacy con porcentaje nulo, representándolo como 0.
- **RF-002** CUANDO `company_boards` está incluido, el sistema DEBE cargar los boards
  soportados configurados en `target-companies` del usuario y devolver resultados o un
  error identificable por board.
- **RF-003** SI se crea una vacante con `vacancy_url` ya existente para el mismo usuario,
  el sistema DEBE responder 409 RFC 9457 y dejar la sesión de BD utilizable.
- **RF-004** El sistema NO DEBE anunciar `content-pieces` como recurso independiente.
- **RF-005** CUANDO una vacante referencia una empresa diana, el sistema DEBE persistir
  una FK válida del mismo usuario y conservar `company` como snapshot legible.
- **RF-006** El CRUD de `identity` DEBE persistir y devolver `modality_priority` y
  `availability_hours`.
- **RF-007** El CRUD de `certifications` DEBE persistir y devolver `completion_date`.
- **RF-008** El CRUD de `role-gap-analysis` DEBE persistir y devolver `target_date`.
- **RF-009** El CRUD de `target-companies` DEBE persistir y devolver los nueve campos
  solicitados con validación de URL y score.
- **RF-010** El CRUD de `vacancies` DEBE persistir y devolver los trece campos
  solicitados, además de `target_company_id`, con constraints de rango y propiedad.
- **RF-011** El CRUD de `portal-about` DEBE persistir y devolver `bio_text`, `headline`
  y `timeline_milestones` con estructura validada.
- **RF-012** PostgreSQL DEBE aplicar las FK `applications→vacancies`,
  `application_interactions→applications` e `interviews→applications` sin huérfanos.
- **RF-013** El Admin DEBE permitir ver y editar todos los campos nuevos usando
  controles adecuados y selectores FK para empresa/contacto.
- **RF-014** `/public/about` y el Portfolio DEBEN mostrar headline, bio y timeline con
  fallback compatible, y la fecha completa de certificación cuando exista.
- **RF-015** La migración DEBE poder subir y bajar sin perder columnas o datos previos;
  debe abortar antes de crear FK si detecta huérfanos.

## 5 · Casos límite y errores

- URL duplicada entre usuarios distintos es válida; dentro del mismo usuario es 409.
- URL NULL no participa en el conflicto.
- Empresa/contacto de otro usuario se rechaza con 400 y no se persiste.
- `salary_min > salary_max`, score fuera de 0..5, años negativos o prioridad/modelo no
  válidos se rechazan con 422.
- JSONB NULL es distinto de lista vacía; ambos se serializan sin 500.
- Board no soportado se ignora con error explícito; un board fallido no cancela los
  demás.
- Timeline vacío no muestra una sección vacía en el portal.

## 6 · Decisiones y descartes

- **D-01:** se conserva `company` como snapshot; eliminarlo sería breaking.
- **D-02:** listas flexibles se guardan en JSONB, no texto delimitado.
- **D-03:** catálogos de negocio siguen siendo strings validados en API/Admin para no
  introducir migraciones por cada valor nuevo.
- **D-04:** `publications` es el único recurso editorial; se corrige documentación.
- **D-05:** las FK físicas faltantes se reparan porque el contrato ORM afirma que ya
  existen; no se deja integridad sólo en aplicación.
- **D-06:** no se cifra `career_board_token`: hoy es un slug público de Greenhouse/Lever,
  no una credencial secreta.

## 7 · Requisitos no funcionales

- **RNF-001:** cobertura mínima 80 % por módulo tocado y objetivo 90 % para código nuevo.
- **RNF-002:** ninguna prueba llama a servicios externos reales salvo la comprobación
  manual de diagnóstico ya documentada.
- **RNF-003:** el despliegue requiere backup, migración, health, smoke API y smoke UI;
  ante fallo se ejecuta downgrade y se restaura la imagen anterior.
