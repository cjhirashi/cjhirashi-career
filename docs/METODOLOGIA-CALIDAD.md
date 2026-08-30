# Metodología de Calidad — cjhirashi-career

Marco de calidad obligatorio del proyecto y flujo de trabajo entre roles. Referenciado desde [`CLAUDE.md`](../CLAUDE.md) — se consulta al escribir código, revisar un PR, o cerrar un módulo; no hace falta en cada turno de conversación.

## Framework de Calidad Integral

| Área | Regla | Responsable |
|---|---|---|
| Documentación | Arc42 (ISO 42010) en `docs/01-12`, ADRs en `docs/09-DECISIONS/` | El Arquitecto decide qué documentar, Documentador redacta |
| Código | SOLID + Clean Code; DDD en lógica compleja | Code Quality Guardian valida, especialista de módulo implementa |
| Testing | Pirámide 60% unit / 30% integration / 10% E2E — **cobertura mínima 80% por módulo** | QA Engineer coordina, especialista escribe tests |
| Code Review | Obligatorio antes de merge, checklist SOLID/Clean Code/tests | Code Quality Guardian |
| CI/CD | Gates: Build → Unit Tests (80%+) → Integration → Code Quality → Security Scan → Performance → Deploy | Experto Docker (pipeline), QA + Guardian (gates) |
| Seguridad | Auditoría de dependencias, escaneo de vulnerabilidades, secretos, OWASP | Code Quality Guardian coordina, especialistas implementan |

Catálogo de agentes que materializan estos roles: [EQUIPO-AGENTES.md](EQUIPO-AGENTES.md).

## Flujo de Trabajo Arquitectónico

**Diseño** (Arquitecto: requisitos → arquitectura → ADR) → **Infraestructura** (Experto Docker: compose/Dockerfiles/redes/CI-CD) → **Documentación** (Arquitecto define qué, Documentador redacta, Arquitecto aprueba) → **Desarrollo** (especialista de módulo → Code Quality Guardian revisa → QA Engineer valida 80% cobertura → Git commit) → **Validación** (CI/CD gates + seguridad + cobertura → merge a `main`).

## Checklist de Calidad por Módulo

Antes de que un módulo sea "listo":

```
☐ Código escrito (SOLID + Clean Code)
☐ Unit tests: 80%+ cobertura
☐ Integration tests: flujos críticos
☐ Code review: aprobado
☐ Security scan: sin vulnerabilidades
☐ Performance: aceptable
☐ Documentación: Arc42 + ADR
☐ README: claro y profesional
☐ CI/CD gates: pasan todos
☐ Integración: funciona con otros módulos
```

Ver también los escenarios de calidad verificables (rendimiento, disponibilidad, seguridad, etc.) en [10-QUALITY-SCENARIOS.md](10-QUALITY-SCENARIOS.md).
