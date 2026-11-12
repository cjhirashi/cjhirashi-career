# Plan de implementación - cjhirashi-career

**Última actualización:** 2026-11-12
**Estado:** en producción; evolución por specs del arnés (`.harness/specs/`).

---

## Resumen

El plan original en tres fases (sistema manual, MCP Server, Agent Bedrock) se cumplió con un recorrido distinto: el sistema manual está en producción, el MCP Server se retiró (ADR-023) y los agentes son externos por la API (ADR-032); el subsistema Bedrock se retiró el 2026-11-11 (ADR-033) y el descubrimiento de vacantes el 2026-11-12 (ADR-034). Desde entonces el trabajo avanza por **specs**: cada una pasa por gates aprobados por Carlos y su estado vive en el `estado:` de su `spec.md`. Este documento resume lo entregado y lo que sigue.

## Entregado (en producción)

| Bloque | Qué incluye | Referencia |
|---|---|---|
| **API REST + PostgreSQL** | JWT, CRUD de carrera (≈48 recursos bajo `/career`), archivos en MinIO, PDF, health checks; 419 operaciones, 58 tablas, 56 migraciones | [`cjhirashi-career-api/`](../cjhirashi-career-api/README.md) |
| **Admin Panel** | 24 pantallas: dashboard, recursos de carrera, archivos, tareas (lista, kanban, calendario, Gantt), PDF, métricas, configuración | [`cjhirashi-career-admin/`](../cjhirashi-career-admin/README.md) |
| **Portal público** | Inicio, Sobre mí, Proyectos, Blog, Contacto, Privacidad | [`cjhirashi-career-portfolio/`](../cjhirashi-career-portfolio/README.md) |
| **Spec 007** | Vacantes: etapa del proceso y estado calculado (verified) | — |
| **Spec 008** | Vacantes: empresa, puesto, oferta y cultura (implemented) | — |
| **Spec 010** | Analítica profesional del portafolio: ingesta, tablero, metas, embudos, API para agentes (implemented) | `.harness/specs/010-portal-analytics/` |
| **Spec 011** | Formulario de contacto → Admin (implemented) | `.harness/specs/011-contact-messages/` |

## En curso

Nada en curso. La spec 009 (harness de agentes fuera de la API) quedó sin efecto al retirarse el subsistema ([ADR-033](./09-DECISIONS/033-retiro-del-subsistema-bedrock.md)).

## Pendiente

| Spec | Estado | Alcance |
|---|---|---|
| **006** | approved (0 de 20 tareas) | Tablas, relaciones y frontends del checklist de carrera |

Mejoras de plataforma identificadas en [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md), por prioridad: respaldo automático de PostgreSQL (R8), expiración y revocación de tokens (R6, R7), escaneo de dependencias en CI (R9).

## Cómo se planifica

- Una feature nueva empieza con `spec.md` (Gate 1), `plan.md` (Gate 2) y `tasks.md`; el estado lo fija el usuario, nunca el agente que implementa.
- La documentación se actualiza en el mismo commit que el código (Constitución Art. 11).
- Método y reglas: [`.harness/method.md`](../.harness/method.md) y [`.harness/constitution.md`](../.harness/constitution.md).

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [04-SOLUTION-STRATEGY.md](./04-SOLUTION-STRATEGY.md) · [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md)
