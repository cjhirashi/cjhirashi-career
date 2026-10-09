---
titulo: "Plan — Career: tablas, relaciones y frontends"
tipo: plan
estado: approved
fecha: 2026-10-09
feature_id: "006"
spec: ./spec.md
---

# Plan de implementación

## 1 · Secuencia y dependencias

1. Cerrar la parte de feature 005 necesaria para que `operational-methodologies` deje
   de seleccionar columnas ya eliminadas.
2. Escribir pruebas rojas de los bugs y de la migración 006.
3. Crear la migración desde head `f8a9b0c1d2e3`: search-plan backfill/constraint,
   campos nuevos, unique por usuario, backfill `target_company_id`, FK nuevas y
   preflight de huérfanos.
4. Actualizar modelos y esquemas.
5. Añadir validación de relaciones del mismo usuario en capa de servicio/repositorio y
   traducción de conflictos a RFC 9457 en la ruta genérica.
6. Fijar pruebas de regresión de company boards sin cambiar el flujo que ya funciona.
7. Actualizar Admin y Portfolio.
8. Sincronizar documentación, ejecutar gate completo y crear commits por bloque.
9. Respaldar, migrar, reconstruir servicios y ejecutar smoke tests en vivo.

## 2 · Implementación por requisito

### RF-001 · Search plans
Test de response con NULL; migración `UPDATE ... SET 0`, default y NOT NULL; modelo y
schema mantienen 0 como default.

### RF-002 · Company boards
Pruebas de `_load_company_boards`, `run_discovery` y payload del Admin. Cada board usa
provider/token públicos, genera nombre de error propio y no cancela los demás.

### RF-003 · Conflictos de vacancy URL
Migración reemplaza unique global por `(user_id, vacancy_url)`. El repositorio hace
rollback ante `IntegrityError`; `career_common` traduce el constraint conocido a 409
RFC 9457 sin esconder otros errores de integridad.

### RF-004 · Content pieces
Eliminar la mención de la referencia de recursos y docs del API. No se agrega ruta.

### RF-005/RF-010 · Vacancies y relaciones
Migración y modelo; validación same-user antes del write para `target_company_id` y
`contact_id`; snapshot de company desde TargetCompany; admin con `fk-select`.

### RF-006–RF-011 · Campos por recurso
Una migración aditiva; modelos SQLAlchemy; Base/Create/Update/Response Pydantic; tipos y
formularios Admin. JSONB se valida como listas sin valores vacíos ni duplicados.

### RF-012 · FK físicas
Preflight SQL de huérfanos; constraints con nombres explícitos y `ON DELETE` igual al
modelo. Documentar todas las columnas, checks, índices y FK.

### RF-013 · Admin
Actualizar `types/career.ts` y `careerResources.ts`. Fechas usan `date`, JSON arrays el
editor JSON/lista disponible, URLs texto con ayuda, scores/salarios number y relaciones
FK selects. Pruebas de configuración y render.

### RF-014 · Portal público
Extender `PublicAboutResponse`, `/public/about`, tipos TS y `AboutPage`. Headline/bio
nuevos prevalecen con fallback; timeline sólo aparece con elementos; certificaciones
prefieren `completion_date` y conservan `year` como fallback.

### RF-015 · Seguridad de migración
Test de SQL emitido, orden de preflight, upgrade/downgrade y constraints. Antes de
producción se toma dump; no se aplica si hay huérfanos o backfill ambiguo no revisado.

## 3 · Estrategia de pruebas

| Capa | Evidencia |
|---|---|
| Migración | revisión/orden SQL, upgrade+downgrade en clon PostgreSQL |
| Modelo/esquema | Pydantic, checks y serialización de NULL/JSONB/Decimal |
| Repositorio/ruta | 409 + rollback, same-user FK, GET sin 500 |
| Servicio | company boards con dobles HTTP/DB |
| Admin | configuración de campos, payload y type-check |
| Portfolio | contrato About, fallback y timeline |
| Sistema | `.harness/gate/check.sh --full`, health y smoke API/UI |

## 4 · Reversión

- Código: revertir commits del bloque afectado y reconstruir sólo los servicios tocados.
- BD: `alembic downgrade f8a9b0c1d2e3`; el downgrade elimina sólo columnas/constraints
  de 006, restaura unique global únicamente si no hay duplicados entre usuarios y
  vuelve a permitir NULL en search plans.
- Datos: dump previo obligatorio. Los backfills sólo completan NULL; no reescriben
  valores del usuario.

## 5 · Impacto en documentación

| Documento | Cambio |
|---|---|
| referencia `career-resources.md` | retirar `content-pieces` |
| `models/README.md` | campos y relaciones nuevas |
| `schemas/README.md` | contratos Create/Update/Response |
| docs de BD/API | esquema real de applications/interactions/interviews |
| `.harness/memory/state.md` | fase, gate y siguiente paso |

No se agrega dependencia de terceros ni se cambia arquitectura.
