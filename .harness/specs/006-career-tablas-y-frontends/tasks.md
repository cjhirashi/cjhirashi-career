---
titulo: "Tasks — Career: tablas, relaciones y frontends"
tipo: tasks
estado: approved
fecha: 2026-10-09
feature_id: "006"
spec: ./spec.md
plan: ./plan.md
---

# Tareas

## A · Baseline y bugs
- [ ] **T-001** `[test]` (RF-001) — GET search plans con porcentaje NULL.
- [ ] **T-002** `[test]` (RF-002) — company boards carga Mutt/Lever y aísla errores.
- [ ] **T-003** `[test]` (RF-003) — duplicado same-user 409 y rollback; otro usuario permitido.
- [ ] **T-004** `[code]` (RF-001–RF-003) — implementación mínima de bugs.
- [ ] **T-005** `[doc]` (RF-004) — retirar `content-pieces`.

## B · Migración y contratos
- [ ] **T-010** `[test]` (RF-005–RF-012, RF-015) — migración roja: columnas, checks,
  unique por usuario, backfill, preflight y FK.
- [ ] **T-011** `[migration]` (RF-005–RF-012, RF-015) — migración upgrade/downgrade.
- [ ] **T-012** `[test]` (RF-006–RF-011) — esquemas y validaciones rojas.
- [ ] **T-013** `[model/schema]` (RF-006–RF-011) — modelos y Pydantic.
- [ ] **T-014** `[test]` (RF-005, RF-010) — relaciones same-user y snapshot company.
- [ ] **T-015** `[service/repo]` (RF-005, RF-010) — validación de relaciones.

## C · Frontends
- [ ] **T-020** `[test]` (RF-013) — configuración Admin de todos los campos y FK.
- [ ] **T-021** `[admin]` (RF-013) — tipos, columnas y formularios.
- [ ] **T-022** `[test]` (RF-014) — contrato About, fallback, timeline y certificación.
- [ ] **T-023** `[api/portfolio]` (RF-014) — endpoint público, tipos y AboutPage.

## D · Documentación, validación y cierre
- [ ] **T-030** `[doc]` (RF-012) — esquema completo de las tres tablas y relaciones.
- [ ] **T-031** `[verify]` (RNF-001/002) — suites focalizadas + gate completo.
- [ ] **T-032** `[commit]` — commits separados de SDD, bugs, BD/API, Admin, Portal/docs.
- [ ] **T-033** `[deploy]` (RNF-003) — backup, migración, rebuild y smoke tests.
- [ ] **T-034** `[close]` — anclas, state/history, wiki y bitácora.

## Cobertura
| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-001, T-004, T-011 | test search plans | pendiente |
| RF-002 | T-002, T-004 | test job discovery | pendiente |
| RF-003 | T-003, T-004, T-011 | test CRUD conflicts | pendiente |
| RF-004 | T-005 | búsqueda documental | pendiente |
| RF-005 | T-010, T-011, T-014, T-015 | migration + relations | pendiente |
| RF-006 | T-010–T-013, T-020–T-021 | schema/admin | pendiente |
| RF-007 | T-010–T-013, T-020–T-023 | schema/admin/public | pendiente |
| RF-008 | T-010–T-013, T-020–T-021 | schema/admin | pendiente |
| RF-009 | T-010–T-013, T-020–T-021 | schema/admin | pendiente |
| RF-010 | T-010–T-015, T-020–T-021 | migration/relations/admin | pendiente |
| RF-011 | T-010–T-013, T-020–T-023 | schema/admin/public | pendiente |
| RF-012 | T-010–T-011, T-030 | migration + doc | pendiente |
| RF-013 | T-020–T-021 | admin config/render | pendiente |
| RF-014 | T-022–T-023 | public route/page | pendiente |
| RF-015 | T-010–T-011, T-031, T-033 | migration/gate/smoke | pendiente |
| doc: resources/schema | T-005, T-030 | — | pendiente |
