# Metas y restricciones arquitectónicas - cjhirashi-career

**METAS ARQUITECTÓNICAS** (arc42, sección 2)

**Última actualización**: 2026-11-05
**Resumen**: 3 objetivos de negocio · 6 objetivos técnicos priorizados · 5 restricciones · 5 convenciones de trabajo.

---

## Propósito

[01-INTRODUCTION.md](./01-INTRODUCTION.md) describe **qué es** el sistema; este documento fija **qué debe lograr** y **qué no es negociable**. Toda decisión posterior (un ADR, la forma de un componente) debe poder justificarse contra uno de estos objetivos o restricciones.

## Objetivos de negocio

| # | Objetivo | Descripción |
|---|---|---|
| 1 | **Portafolio profesional** | Presencia pública curada y siempre al día: un proyecto, logro o publicación nuevo aparece en el portal sin mantenimiento web adicional. |
| 2 | **Gestión centralizada de carrera** | Una sola fuente de verdad para identidad, competencias, evidencia, vacantes, contactos y entrevistas, en lugar de documentos y hojas sueltas. |
| 3 | **Operación asistida por agentes de IA** | Que agentes (Agent Bedrock dentro del Admin y agentes externos con token `agent`) lean el contexto de carrera y registren actualizaciones sin que Carlos esté frente al panel. |

## Objetivos técnicos (en orden de prioridad)

Ante un conflicto entre dos objetivos, gana el de menor número.

| Prioridad | Atributo | Objetivo |
|---|---|---|
| 1 | **Independencia de canales** | Portal y Admin operan como puntos de entrada autónomos que convergen solo en la API y la base de datos; si uno falla, el otro sigue. |
| 2 | **SPA operativa** | El Admin es una aplicación de una sola página completa: CRUD de todas las entidades de carrera, métricas y chat con agentes, sin flujos rotos entre secciones. |
| 3 | **Observabilidad** | El Admin muestra el tráfico del portal (analítica), la actividad de los agentes (uso, costos, tareas, auditoría) y los errores registrados. |
| 4 | **Escalabilidad horizontal de la API** | Objetivo de diseño: la API es el único punto de convergencia y no guarda estado en memoria que impida replicarla. Hoy corre una sola instancia. |
| 5 | **Aislamiento entre lo privado y lo publicable** | Los datos de gestión no curados (p. ej. una vacante en negociación) nunca llegan al canal público; el portal solo lee lo publicable. |
| 6 | **Control de acceso proporcional** | Sin autenticación para la lectura pública (con límites de tasa), JWT completo para el Admin y un rol `agent` acotado a `/career/*`, el chat de Bedrock y la subida de archivos. |

## Restricciones

| Tipo | Restricción | Justificación |
|---|---|---|
| **Técnica** | Stack fijo: React + TypeScript (frontends), FastAPI (API), PostgreSQL (persistencia) | Continuidad técnica y decisión del arquitecto. |
| **Infraestructura** | Contenedores Docker orquestados con `docker-compose.yml`, en la red externa `net-cjhirashi-career` | Despliegue reproducible con un solo compose. |
| **Calidad** | Cobertura de pruebas mínima del 80 % por módulo | Estándar del arnés, comprobado por el gate. |
| **Datos** | La API es la única que lee y escribe la base de carrera; los agentes la usan solo por la API REST | El harness futuro (`cjhirashi-career-ai`) tendrá su propia base y no accederá a `career_db` ([ADR-029](./09-DECISIONS/029-harness-agentes-fuera-de-api.md)). |
| **Seguridad** | Prácticas OWASP en todo lo expuesto a Internet (Portal, Admin y archivos públicos) | Son alcanzables desde fuera de la red interna. |

## Convenciones de trabajo

El repo usa un arnés SDD Anchored (`.harness/`: método, constitución, specs, memoria). Resumen operativo:

| Convención | Descripción |
|---|---|
| **Spec antes que código** | Lo no trivial pasa por `spec.md` → `plan.md` → `tasks.md` con gates aprobados por el usuario; nada se marca `verified` sin su aprobación. |
| **Documentación en el mismo commit** | Todo cambio actualiza los docs que deja obsoletos (arc42, ADRs, READMEs, `docker-compose.yml`) o declara `Docs actualizadas: ninguna — <motivo>` (Constitución Art. 11; el gate lo exige). |
| **Conventional Commits** | `feat:`, `fix:`, `docs:`… con sufijo `(RF-NNN)` cuando aplica. |
| **Pruebas trazables** | Cada prueba anota su requisito (`@pytest.mark.requisito("RF-014")`, `describe("RF-014: …")`). |
| **Arquitectura por capas** | `routes → services → repositories → models`. Norma del arnés: errores de API nuevos en Problem Details (RFC 9457); la API existente responde `{"detail": …}` (formato estándar de FastAPI) y registra los fallos en `error_reports`. |

## Relación con otras secciones

[01-INTRODUCTION.md](./01-INTRODUCTION.md) (el sistema) · [03-STAKEHOLDERS.md](./03-STAKEHOLDERS.md) (quién se beneficia) · [04-SOLUTION-STRATEGY.md](./04-SOLUTION-STRATEGY.md) (cómo se cumplen) · [09-DECISIONS/](./09-DECISIONS/README.md) (decisiones formales).

---

**Relacionado**: [CLAUDE.md](../CLAUDE.md) · [`.harness/constitution.md`](../.harness/constitution.md)
**Contacto**: cjhirashi@gmail.com
