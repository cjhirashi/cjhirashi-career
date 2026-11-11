# Plan de implementación - cjhirashi-career

> **Estado (2026-11-10, [ADR-032](09-DECISIONS/032-agentes-externos-y-bedrock-fuera-de-operacion.md)):** el subsistema de agentes con AWS Bedrock está **fuera de operación**. Los agentes de IA son externos y entran por la API con el rol `agent`. Este documento se conserva como referencia del diseño y no describe el comportamiento operativo actual.

**Última actualización:** 2026-11-10
**Estado:** en producción; evolución por specs del arnés (`.harness/specs/`).

---

## Resumen

El plan original en tres fases (sistema manual, MCP Server, Agent Bedrock) se cumplió con un recorrido distinto: el sistema manual y Agent Bedrock están en producción, y el MCP Server se retiró (ADR-023). Desde entonces el trabajo avanza por **specs**: cada una pasa por gates aprobados por Carlos y su estado vive en el `estado:` de su `spec.md`. Este documento resume lo entregado y lo que sigue.

## Entregado (en producción)

| Bloque | Qué incluye | Referencia |
|---|---|---|
| **API REST + PostgreSQL** | JWT, CRUD de carrera (≈48 recursos bajo `/career`), archivos en MinIO, PDF, health checks; 419 operaciones, 69 modelos, 53 migraciones | [`cjhirashi-career-api/`](../cjhirashi-career-api/README.md) |
| **Admin Panel** | 24 pantallas: dashboard, recursos de carrera, descubrimiento de vacantes, archivos, tareas (lista, kanban, calendario, Gantt), PDF, métricas, agentes, configuración | [`cjhirashi-career-admin/`](../cjhirashi-career-admin/README.md) |
| **Portal público** | Inicio, Sobre mí, Proyectos, Blog, Contacto, Privacidad | [`cjhirashi-career-portfolio/`](../cjhirashi-career-portfolio/README.md) |
| **Agent Bedrock** | Harness local, jerarquía L1/L2/L3, perfiles configurables, memoria, tareas programadas y subtareas, costos y presupuesto | [BEDROCK-SYSTEM.md](./BEDROCK-SYSTEM.md) |
| **Spec 001** | Sidebar contextual por sección (verified) | ADR-024 |
| **Spec 002** | Generación de imágenes del agente Visual (verified) | ADR-025 |
| **Specs 003 y 004** | Configuración de agentes desde la App; herramientas y metodologías por sección (verified) | ADR-026, ADR-027 |
| **Spec 007** | Vacantes: etapa del proceso y estado calculado (verified) | — |
| **Spec 008** | Vacantes: empresa, puesto, oferta y cultura (implemented) | — |
| **Spec 010** | Analítica profesional del portafolio: ingesta, tablero, metas, embudos, API para agentes (implemented) | `.harness/specs/010-portal-analytics/` |
| **Spec 011** | Formulario de contacto → Admin (implemented) | `.harness/specs/011-contact-messages/` |

## En curso

**Spec 009 — Harness de agentes fuera de la API y sin indexación** (ADR-029; `approved`, 62 de 163 tareas). Tres etapas reversibles:

1. **Harness arriba, datos copiados**: `cjhirashi-career-ai` con su base `career_ai_db`, cambios aditivos de la API (claim `role`, rol `service`, `/notifications`, `/audit-log`) y migración de la memoria del agente. *No iniciada en producción.*
2. **El Admin llama al harness** bajo `/ai/` con paridad exacta del contrato `/bedrock/*` y `/agent-tasks/*`.
3. **Retiro de la API**: se elimina Bedrock y la migración borra las tablas `bedrock_*` de `career_db` solo tras verificar la copia.

Qdrant y la KB ya se retiraron (2026-11-11, ADR-032).

## Pendiente

| Spec | Estado | Alcance |
|---|---|---|
| **005** | draft (2 de 45 tareas) | Metodologías: esquema mínimo y vínculo con secciones editable desde la app |
| **006** | approved (0 de 20 tareas) | Tablas, relaciones y frontends del checklist de carrera |

Mejoras de plataforma identificadas en [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md), por prioridad: respaldo automático de PostgreSQL (R8), expiración y revocación de tokens (R6, R7), escaneo de dependencias en CI (R9).

## Cómo se planifica

- Una feature nueva empieza con `spec.md` (Gate 1), `plan.md` (Gate 2) y `tasks.md`; el estado lo fija el usuario, nunca el agente que implementa.
- La documentación se actualiza en el mismo commit que el código (Constitución Art. 11).
- Método y reglas: [`.harness/method.md`](../.harness/method.md) y [`.harness/constitution.md`](../.harness/constitution.md).

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [04-SOLUTION-STRATEGY.md](./04-SOLUTION-STRATEGY.md) · [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md)
