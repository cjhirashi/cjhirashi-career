# Usuarios, roles y expectativas - cjhirashi-career

**STAKEHOLDERS** (arc42, sección 3)

**Última actualización**: 2026-11-05

---

## Propósito

Identifica **quién interactúa con el sistema y con el proyecto**, qué necesita y qué espera. Es la contraparte humana de [02-ARCHITECTURE-GOALS.md](./02-ARCHITECTURE-GOALS.md). Tres categorías: **usuarios**, **equipo de desarrollo** e **infraestructura**.

## Usuarios

| Stakeholder | Canal | Qué necesita | Qué espera |
|---|---|---|---|
| **Carlos Jiménez Hirashi** (gestor de carrera, único administrador) | Admin Panel (`admin.cjhirashi.com`), con login | Registrar y mantener toda su carrera en un solo lugar y delegar redacción o análisis a los agentes cuando quiera | Un panel rápido y confiable; que no se pierda nada entre la gestión manual y la asistida; visibilidad real del tráfico del portal, la actividad de los agentes y los errores |
| **Visitantes** (reclutadores, colegas, público) | Portal público (`cjhirashi.com`), sin cuenta | Conocer el perfil profesional (Sobre mí, Proyectos, Blog) y poder escribirle por el formulario de contacto | Contenido siempre actualizado, carga rápida y privacidad: pueden borrar sus datos de analítica en `/privacy` |
| **Agentes de IA** (Agent Bedrock dentro del Admin; agentes externos con token `agent`) | API REST: Bedrock vía `/bedrock/*`; los externos, `/career/*`, `POST /bedrock/chat` y `POST /files` | Un contrato de API estable para leer y escribir el contexto de carrera (los externos también suben diagramas o imágenes) | Respuestas predecibles; que su actividad quede auditada y medible en el Admin |

## Equipo de desarrollo

El repo se trabaja con un arnés SDD Anchored (`.harness/method.md §8`). Roles base: **orquestador**, **autor de spec**, **arquitecto**, **implementador**, **revisor** y **explorador**; especialista: **experto UX/UI**, que revisa toda feature de interfaz antes de `verified` (Constitución Art. 8). Los stubs viven en `.claude/agents/`.

| Rol | Qué necesita | Qué espera |
|---|---|---|
| **Carlos (arquitecto y aprobador)** | Trazabilidad de cada decisión y specs claras para aprobar en cada gate | Que nadie marque `verified` sin su aprobación y que las desviaciones se escalen |
| **Orquestador / autor de spec / arquitecto** | El método y la constitución como contrato | Specs completas antes de implementar |
| **Implementador y revisor** | Specs, planes y tareas con criterios verificables | Pruebas que respalden cada requisito y revisión adversarial antes de cerrar |
| **Experto UX/UI** | Capturas reales del resultado y las referencias de diseño vigentes | Que ninguna interfaz pase a `verified` sin su revisión |

## Infraestructura

| Stakeholder | Qué necesita | Qué espera |
|---|---|---|
| **`cjhirashi-srv`** (proxy compartido: Caddy + Cloudflare Tunnel) | `caddy.json` vigente con hosts, contenedores y puertos de cada servicio | Que solo Portal, Admin y archivos públicos se expongan; API, PostgreSQL y Qdrant no se publican |
| **CI** (GitHub Actions) | Pruebas del subsistema Bedrock de la API (Python 3.11) y build del Admin (Node 20) | Que los cambios pasen la compuerta antes de integrarse |

## Matriz de prioridades

| Momento | Quién prioriza | Impacto de no priorizarlo |
|---|---|---|
| **Diseño y decisiones** | Carlos, con el arquitecto | Specs construidas sobre supuestos distintos |
| **Aprobación de cada gate** | Carlos | Código sin respaldo aprobado |
| **Uso diario del Admin** | Carlos | Un panel poco usable rompe el objetivo de gestión centralizada |
| **Disponibilidad del portal** | Visitantes | No tienen vía de reporte directa; dependen de que funcione sin intervención |
| **Autorización de los agentes** | Carlos (dueño de los datos) | Un agente mal configurado puede escribir datos de carrera sin supervisión en tiempo real |
| **Red y exposición compartida** | `cjhirashi-srv` | Un cambio de puertos o red no coordinado rompe el proxy de otros proyectos |

## Comunicación y feedback

| Stakeholder | Canal | Frecuencia |
|---|---|---|
| Carlos | Uso directo del Admin y conversación con los agentes de trabajo | Continua |
| Visitantes | Sin canal directo: mensajes del formulario de contacto y analítica agregada | Pasiva |
| Agentes de IA | Auditoría, métricas de agentes y registro de errores en el Admin | Pasiva |
| Equipo de desarrollo | Specs y estado en `.harness/`; commits y `history.md` | Por cada entregable |
| `cjhirashi-srv` | Mensajes del contrato `caddy.json` | Ante cambios de exposición |

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [02-ARCHITECTURE-GOALS.md](./02-ARCHITECTURE-GOALS.md) · [04-SOLUTION-STRATEGY.md](./04-SOLUTION-STRATEGY.md) · [CLAUDE.md](../CLAUDE.md)
**Contacto**: cjhirashi@gmail.com
