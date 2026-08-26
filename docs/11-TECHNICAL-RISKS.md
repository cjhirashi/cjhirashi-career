# Riesgos Técnicos y Mitigación - cjhirashi-career

**RIESGOS TÉCNICOS**

[![Document Type](https://img.shields.io/badge/type-architecture-blue)]()
[![Audience](https://img.shields.io/badge/audiencia-arquitectos%20%7C%20developers%20%7C%20stakeholders-informational)]()
[![Estado](https://img.shields.io/badge/estado-diseño%20en%20validación-yellow)]()

---

**Última actualización**: 2026-08-16
**Resumen rápido**: 10 riesgos del nuevo alcance de portafolio · 2 riesgos adicionales identificados en el código heredado todavía vigente · 3 riesgos de impacto crítico requieren mitigación antes de manejar datos reales de carrera profesional

---

## 📋 Tabla de Contenidos

- [Cómo Leer Este Documento](#-cómo-leer-este-documento)
- [Riesgos del Nuevo Alcance](#-riesgos-del-nuevo-alcance)
- [Riesgos Adicionales del Código Heredado](#-riesgos-adicionales-del-código-heredado)
- [Matriz de Priorización](#-matriz-de-priorización)
- [Orden de Atención Recomendado](#-orden-de-atención-recomendado)

---

## 📖 Cómo Leer Este Documento

Este documento es la sección 11 de la documentación Arc42 y responde a **qué puede salir mal en el nuevo alcance de cjhirashi-career y cómo se previene o mitiga**. No repite el detalle de cada componente ya cubierto en `01-INTRODUCTION.md` a `08-CROSSCUTTING-CONCEPTS.md`, ni el estado de cada atributo de calidad de [10-QUALITY-SCENARIOS.md](./10-QUALITY-SCENARIOS.md); traduce ambos a **riesgo** — probabilidad de que cause un problema real una vez que el sistema esté implementado y en uso, impacto si ocurre, y la mitigación concreta.

**Probabilidad** se evalúa en escala Alta / Media / Baja como la probabilidad de que el riesgo **cause un incidente** una vez el sistema esté construido y operando con datos reales de carrera profesional — no la probabilidad de que la condición de riesgo ya exista hoy en el diseño (varias sí existen ya, como riesgos de diseño a mitigar antes de implementar). **Impacto** usa la misma escala, más un nivel **Crítico** reservado para riesgos que comprometerían datos personales o credenciales de forma irreversible.

## ⚠️ Riesgos del Nuevo Alcance

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|:---:|:---:|-------------|
| R1 | La complejidad del Admin Panel (SPA con cinco secciones, estado compartido, tiempo real y chat con Bedrock) crece sin controles de arquitectura, generando componentes acoplados y difíciles de mantener | Alta | Alta | Code review obligatorio contra el checklist de SOLID/Clean Code de `CLAUDE.md`, cobertura de tests mínima del 80% desde el primer commit del módulo (ver [08-CROSSCUTTING-CONCEPTS — Testing](./08-CROSSCUTTING-CONCEPTS.md#-testing)), y respetar la separación ya definida en [05-BUILDING-BLOCK-VIEW — Nivel 2: Admin Panel](./05-BUILDING-BLOCK-VIEW.md#-nivel-2--descomposición-del-admin-panel) (Navigation, CRUD, Metrics, Chat, Config, Logs como bloques independientes) |
| R2 | El volumen de eventos de `mcp_agent_metrics`, `portal_visits` y `portal_interactions` excede la capacidad razonable de la instancia única de PostgreSQL | Media | Alta | Archivado automático más allá de la retención de 90 días ya definida en [08-CROSSCUTTING-CONCEPTS — Sistema de Métricas](./08-CROSSCUTTING-CONCEPTS.md#-sistema-de-métricas), e índices ya especificados en [05-BUILDING-BLOCK-VIEW — Relaciones e Índices Clave](./05-BUILDING-BLOCK-VIEW.md#relaciones-e-índices-clave) (`idx_mcp_metrics_request_at`, `idx_portal_visits_visited_at`); ver también el objetivo de volumen (E3) en [10-QUALITY-SCENARIOS.md](./10-QUALITY-SCENARIOS.md#-escalabilidad) |
| R3 | La sincronización entre el MCP Server y la API REST falla a mitad de una operación (por ejemplo, el MCP Server confirma al agente externo antes de que la escritura se persista) | Media | Alta | Retry logic con backoff en la llamada del MCP Server hacia la API REST, y no confirmar al agente externo hasta recibir la confirmación de persistencia (`INSERT`/`UPDATE` + `audit_logs`) de la API REST — coherente con el flujo síncrono ya descrito en [06-RUNTIME-VIEW — Escenario 5](./06-RUNTIME-VIEW.md#-escenario-5--agente-externo-opera-vía-mcp-server) |
| R4 | El canal de tiempo real (`/api/v1/metrics/stream`) sufre desconexiones frecuentes, dejando el Metrics Dashboard con datos obsoletos sin que Carlos Jiménez Hirashi lo note | Media | Media | Reconexión automática con backoff en el cliente del Admin Panel, con `RealtimeIndicator` visible mostrando el estado de la conexión (conectado / reconectando / caído), y *fallback* a *polling* periódico vía `GET /api/v1/metrics/*` mientras la conexión en vivo no esté disponible — ver requisito ya definido en [08-CROSSCUTTING-CONCEPTS — Tiempo Real](./08-CROSSCUTTING-CONCEPTS.md#-tiempo-real) |
| R5 | Una fuga de datos entre usuarios permite que una consulta devuelva o modifique información de carrera de un usuario distinto al autenticado | Baja | Crítico | Row-Level Security (RLS) a nivel de PostgreSQL como capa de defensa adicional a la ya definida en [08-CROSSCUTTING-CONCEPTS — Autenticación y Autorización](./08-CROSSCUTTING-CONCEPTS.md#-autenticación-y-autorización) (filtro por `user_id` en cada consulta de la capa de Services); RLS no está implementado hoy — el aislamiento actual depende exclusivamente del filtro a nivel de aplicación, lo que deja este riesgo en probabilidad baja pero no nula mientras no exista una segunda capa de control en la base de datos |
| R6 | Un agente de IA externo, vía MCP Server, envía datos malformados o inconsistentes que corrompen una entidad de carrera (por ejemplo, una vacante sin estado válido) | Media | Media | Validación de payload contra JSON Schema antes de que la operación llegue a la capa de Services, y ejecución de cada mutación dentro de una transacción que solo hace *commit* si toda la operación (incluida la entrada de `audit_logs`) es válida — ver el punto de mayor sensibilidad del sistema, ya señalado como pregunta abierta en [01-INTRODUCTION — Preguntas de Validación Abiertas #1](./01-INTRODUCTION.md#-preguntas-de-validación-abiertas) |
| R7 | Un JWT del Admin Panel es comprometido (robado o filtrado) y usado para operar el sistema suplantando a Carlos Jiménez Hirashi | Baja | Crítico | Rotación periódica de `SECRET_KEY` y una expiración de token más corta (objetivo <24 horas, ver escenario S2 en [10-QUALITY-SCENARIOS.md](./10-QUALITY-SCENARIOS.md#-seguridad)), junto con una lista de revocación (*blacklist*) de tokens invalidados antes de su expiración natural — ninguno de los dos mecanismos existe hoy; el valor heredado (`ACCESS_TOKEN_EXPIRE_DAYS=7`) amplía la ventana de exposición si un token se filtra |
| R8 | PostgreSQL sufre corrupción de datos (fallo de disco, apagado abrupto del contenedor) sin posibilidad de restaurar el estado previo | Baja | Crítico | Backups diarios automatizados y replicación WAL (*Write-Ahead Logging*) hacia un destino distinto del volumen principal — ninguno de los dos está definido hoy; ver la brecha explícita en [07-DEPLOYMENT-VIEW — Ambiente de Producción](./07-DEPLOYMENT-VIEW.md#-ambiente-de-producción) ("sin réplicas ni backups automatizados definidos") |
| R9 | Una dependencia de terceros (React, FastAPI, SQLAlchemy, boto3, WeasyPrint u otra) introduce una vulnerabilidad conocida (CVE) en cualquiera de los siete módulos | Alta | Media | Escaneo automático de dependencias (por ejemplo, Dependabot o equivalente) como parte del gate de CI/CD obligatorio definido en `CLAUDE.md`, responsabilidad conjunta del Experto Docker (configuración del pipeline) y Code Quality Guardian (validación del resultado) |
| R10 | El servicio gestionado de AWS Bedrock está indisponible o inalcanzable (problema de red, límite de cuota, incidente de AWS) | Media | Baja | Degradación controlada (*graceful degradation*): el Admin Panel debe seguir siendo completamente funcional para gestión manual de carrera cuando Agent Bedrock no responde — el Chat Bedrock se deshabilita o muestra un estado de error, sin bloquear el resto de las cinco secciones del panel (ver independencia funcional ya implícita en [05-BUILDING-BLOCK-VIEW — Admin Panel Detallado](./05-BUILDING-BLOCK-VIEW.md#-admin-panel-detallado)) |

## 🔍 Riesgos Adicionales del Código Heredado

Riesgos detectados en el código real presente hoy en el repositorio (alcance anterior de generador de documentos), que siguen vigentes mientras ese código sirva de base técnica al nuevo alcance:

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|:---:|:---:|-------------|
| R11 | Brecha total entre el diseño Arc42 del nuevo alcance (`01-INTRODUCTION.md` a `08-CROSSCUTTING-CONCEPTS.md`) y el código real del repositorio, que todavía implementa el alcance anterior (generador de CV/Cover Letter de 5 módulos, sin Portal Público, Admin Panel, Agent Bedrock ni tablas de carrera) | Alta (ya vigente) | Alta | Planificar la implementación del nuevo alcance como un proyecto de migración explícito, no como una serie de parches sobre el código heredado — empezando por el modelo de datos (`05-BUILDING-BLOCK-VIEW — Base de Datos Detallada`) y la API REST reestructurada en capas (`Controllers → Services → Repository → Models`), antes de tocar los tres frontends |
| R12 | Secretos en texto plano versionados en `docker-compose.yml` real (`SECRET_KEY: mcp-secret-key-change-in-production-32chars-min`, `POSTGRES_PASSWORD: mcppass123`) | Alta (ya vigente) | Alta | Mover a un archivo `.env` no versionado o a un gestor de secretos antes de cualquier despliegue del nuevo alcance; rotar ambos valores en el momento del cambio — ver [10-QUALITY-SCENARIOS.md — S5](./10-QUALITY-SCENARIOS.md#-seguridad) y [07-DEPLOYMENT-VIEW — Ambiente de Producción](./07-DEPLOYMENT-VIEW.md#-ambiente-de-producción) |

## 🧭 Matriz de Priorización

Cruce de **probabilidad** contra **impacto**, coherente con la escala Alta/Media/Baja/Crítico usada en las tablas anteriores. El nivel Crítico se trata como una fila propia por representar el mayor daño posible (compromiso irreversible de datos personales o credenciales), sin importar cuán baja sea su probabilidad:

| | Prob. Baja | Prob. Media | Prob. Alta |
|---|---|---|---|
| **Impacto Crítico** | R5 (fuga de datos entre usuarios), R7 (JWT comprometido), R8 (corrupción de PostgreSQL) | — | — |
| **Impacto Alto** | — | R2 (volumen de eventos), R3 (sincronización MCP↔API) | R1 (complejidad del Admin Panel), R11 (brecha diseño/código) |
| **Impacto Medio** | — | R4 (desconexiones de tiempo real), R6 (datos malformados vía MCP) | R9 (vulnerabilidades de dependencias) |
| **Impacto Bajo** | — | R10 (Bedrock indisponible) | — |
| **(código heredado)** | — | — | R12 (secretos en texto plano) |

## 🎯 Orden de Atención Recomendado

Priorizando primero los riesgos de **impacto Crítico** (sin importar su probabilidad, por el carácter irreversible del daño), luego los de impacto Alto con mayor probabilidad, y dejando para el final los de impacto Bajo:

1. **R12 — Secretos en texto plano (código heredado, ya vigente)**: esfuerzo bajo, bloqueante de cualquier despliegue del nuevo alcance que reutilice esta base técnica.
2. **R7 — JWT sin rotación ni expiración corta**: debe resolverse en el mismo ADR que fije el mecanismo de autenticación del Admin Panel (ver `09-DECISIONS/`), antes de exponer el flujo de login a datos reales de carrera.
3. **R5 — Aislamiento de usuario solo a nivel de aplicación**: aceptable como riesgo de probabilidad baja mientras el sistema tenga un único usuario administrador, pero evaluar RLS antes de considerar cualquier escenario multiusuario futuro.
4. **R8 — Sin estrategia de backup/WAL para PostgreSQL**: definir antes de que el sistema almacene datos reales de carrera profesional — la pérdida de esos datos no es recuperable sin un backup previo.
5. **R11 — Brecha entre diseño y código real**: es el riesgo estructural más grande del proyecto en este momento; condiciona el orden en que se puede atacar todo lo demás (no tiene sentido optimizar R1–R4 sobre un Admin Panel que no existe todavía).
6. **R1 — Complejidad creciente del Admin Panel**: mitigar desde el primer commit del módulo, no después — es más barato mantener la separación en bloques desde el diseño que refactorizar una SPA ya acoplada.
7. **R9 — Vulnerabilidades de dependencias**: configurar el escaneo automático como parte del pipeline de CI/CD desde el inicio del desarrollo del nuevo alcance, en paralelo a R11.
8. **R3 y R6 — Riesgos de la escritura autónoma vía MCP Server**: atender junto con la resolución de la pregunta abierta de autorización del MCP Server (ver [01-INTRODUCTION.md](./01-INTRODUCTION.md#-preguntas-de-validación-abiertas)).
9. **R2 y R4 — Observabilidad y tiempo real**: relevantes en cuanto el Admin Panel y el sistema de métricas tengan tráfico real que evaluar.
10. **R10 — Indisponibilidad de Bedrock**: baja urgencia, pero debe implementarse la degradación controlada desde el primer release del Chat Bedrock, no como un parche posterior.

---

**Relacionado**: [05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md) · [06-RUNTIME-VIEW.md](./06-RUNTIME-VIEW.md) · [07-DEPLOYMENT-VIEW.md](./07-DEPLOYMENT-VIEW.md) · [08-CROSSCUTTING-CONCEPTS.md](./08-CROSSCUTTING-CONCEPTS.md) · [09-DECISIONS/README.md](./09-DECISIONS/README.md) · [10-QUALITY-SCENARIOS.md](./10-QUALITY-SCENARIOS.md) · [CLAUDE.md](../CLAUDE.md)
**Contacto**: Carlos Jiménez Hirashi (cjhirashi@gmail.com)
