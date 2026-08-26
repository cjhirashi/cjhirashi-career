# Escenarios de Calidad y Atributos - cjhirashi-career

**ESCENARIOS DE CALIDAD**

[![Document Type](https://img.shields.io/badge/type-architecture-blue)]()
[![Audience](https://img.shields.io/badge/audiencia-arquitectos%20%7C%20developers%20%7C%20stakeholders-informational)]()
[![Estado](https://img.shields.io/badge/estado-diseño%20en%20validación-yellow)]()

---

**Última actualización**: 2026-08-16
**Resumen rápido**: 6 atributos de calidad · 22 escenarios definidos para el nuevo alcance de portafolio · 2 cumplidos hoy (documentación, no código), 4 parciales (heredados o diseñados pero no verificados), 16 pendientes

---

## 📋 Tabla de Contenidos

- [Cómo Leer Este Documento](#-cómo-leer-este-documento)
- [Rendimiento](#-rendimiento)
- [Disponibilidad](#-disponibilidad)
- [Mantenibilidad](#-mantenibilidad)
- [Seguridad](#-seguridad)
- [Escalabilidad](#-escalabilidad)
- [Usabilidad](#-usabilidad)
- [Resumen de Estado](#-resumen-de-estado)

---

## 📖 Cómo Leer Este Documento

Este documento es la sección 10 de la documentación Arc42 y define **qué significa "calidad" para el nuevo alcance de cjhirashi-career** en términos verificables — no aspiraciones genéricas, sino escenarios concretos con un estímulo, una respuesta esperada y una medida. El marco de calidad de referencia es `CLAUDE.md` (Arc42, SOLID, testing 80%, code review, CI/CD, seguridad); este documento traduce ese marco en escenarios evaluables para los tres canales, Agent Bedrock y PostgreSQL descritos en `01-INTRODUCTION.md` a `08-CROSSCUTTING-CONCEPTS.md`.

**Advertencia honesta sobre el estado del sistema**: el nuevo alcance (Portal Público, Admin Panel, Agent Bedrock, tablas de carrera/observabilidad/auditoría, MCP Server con herramientas de gestión de carrera) es hoy **exclusivamente diseño** — ninguno de esos componentes existe en el código del repositorio. El código real presente hoy (`api/`, `server/`, `docker-compose.yml`) corresponde al **alcance anterior** de este proyecto (generador de documentos CV/Cover Letter), que se conserva como base técnica reutilizable pero no implementa ninguna de las capacidades de carrera profesional, métricas o Agent Bedrock descritas en este Arc42. Por esa razón, la gran mayoría de los escenarios siguientes están marcados como `❌ Pendiente` de forma honesta, y los pocos marcados como `⚠️ Parcial` lo están porque un patrón de la implementación anterior (JWT, CORS, health checks, PostgreSQL como único almacén) es reutilizable pero no ha sido verificado contra el nuevo alcance.

Cada escenario se presenta con cuatro campos — **Estímulo** (qué dispara la evaluación), **Respuesta esperada / Medida** (el umbral concreto), **Estado actual** (✅ Cumple / ⚠️ Parcial / ❌ Pendiente) y **Evidencia** (dónde se verifica).

## ⚡ Rendimiento

| # | Escenario | Estímulo | Respuesta esperada / Medida | Estado | Evidencia |
|---|-----------|----------|-------------------------------|--------|-----------|
| P1 | Carga del Admin Panel | Carlos Jiménez Hirashi navega al Admin Panel y espera a que la SPA sea interactiva | Tiempo hasta interactividad (*Time to Interactive*, TTI) menor a 2 segundos en el percentil 95 (P95) | ❌ Pendiente — no medido | El Admin Panel no existe todavía en el repositorio (ver [05-BUILDING-BLOCK-VIEW — Admin Panel Detallado](./05-BUILDING-BLOCK-VIEW.md#-admin-panel-detallado)); sin build ni entorno donde ejecutar un *benchmark* de TTI |
| P2 | Actualización de métricas en vivo | Un evento nuevo (solicitud del MCP Agent o visita del Portal) se persiste en PostgreSQL | El evento aparece en el Metrics Dashboard del Admin Panel en menos de 500 ms desde la persistencia | ❌ Pendiente — no medido | Objetivo de diseño explícito en [06-RUNTIME-VIEW — Latencias Esperadas](./06-RUNTIME-VIEW.md#latencias-esperadas-objetivo) y en [02-ARCHITECTURE-GOALS — Objetivo técnico #3](./02-ARCHITECTURE-GOALS.md#-objetivos-técnicos); el canal WebSocket/SSE (`/api/v1/metrics/stream`) no está implementado |
| P3 | Respuesta de la API REST | Un canal (Portal, Admin Panel o MCP Server) hace una petición CRUD o de lectura a la API REST | Latencia P95 menor a 200 ms | ❌ Pendiente — sin objetivo formal previo ni medición | No existe todavía este umbral en [02-ARCHITECTURE-GOALS.md](./02-ARCHITECTURE-GOALS.md#-objetivos-técnicos), que hoy prioriza "escalabilidad horizontal" sin fijar una cifra de latencia; se registra aquí como candidato a incorporar formalmente a esa sección |
| P4 | Respuesta del MCP Server | Un agente de IA externo invoca una herramienta MCP de gestión de carrera | El MCP Server responde en menos de 5 segundos en el percentil 95 (P95) | ❌ Pendiente — no medido | Las herramientas MCP de carrera profesional (identidad, competencias, evidencia, vacantes, networking, entrevistas) no existen todavía — el MCP Server heredado solo expone `crear_cv_pdf` y `crear_cover_letter_pdf`, sin instrumentación de latencia (ver [01-INTRODUCTION — Nota de estado actual](./01-INTRODUCTION.md#-diagrama-del-sistema)) |

**Lectura**: el rendimiento es, igual que en la revisión anterior de este documento, el atributo menos maduro — pero ahora por un motivo distinto: no porque falte instrumentación sobre código existente, sino porque el código del nuevo alcance todavía no se ha escrito.

## 🟢 Disponibilidad

| # | Escenario | Estímulo | Respuesta esperada / Medida | Estado | Evidencia |
|---|-----------|----------|-------------------------------|--------|-----------|
| D1 | Disponibilidad del sistema (objetivo MVP) | El sistema opera en producción durante un período sostenido | 99.5% de disponibilidad | ❌ Pendiente — sin objetivo formal ni medición | No hay SLA definido en [02-ARCHITECTURE-GOALS.md](./02-ARCHITECTURE-GOALS.md); no hay monitoreo de *uptime* externo configurado; se registra aquí como el objetivo de disponibilidad de referencia para el MVP |
| D2 | Recuperación ante incidente (RTO) | Un componente crítico (API REST o PostgreSQL) falla y debe restaurarse | Tiempo de recuperación (*Recovery Time Objective*) menor a 1 hora | ❌ Pendiente — sin runbook ni ensayo de recuperación | [07-DEPLOYMENT-VIEW.md](./07-DEPLOYMENT-VIEW.md) no define un procedimiento de recuperación ante desastre; solo describe `restart: unless-stopped` a nivel de contenedor |
| D3 | Pérdida máxima de datos aceptable (RPO) | PostgreSQL sufre una falla que requiere restaurar desde respaldo | Pérdida de datos menor a 5 minutos (*Recovery Point Objective*) | ❌ Pendiente — sin estrategia de backup definida | [07-DEPLOYMENT-VIEW — Ambiente de Producción](./07-DEPLOYMENT-VIEW.md#-ambiente-de-producción): "sin réplicas ni backups automatizados definidos en este documento — pendiente de diseño" |
| D4 | Detección de contenedor caído | Un contenedor del nuevo alcance deja de responder | Docker lo detecta vía `HEALTHCHECK` y puede reiniciarlo (`restart: unless-stopped`) | ⚠️ Parcial — patrón heredado, no verificado sobre el nuevo alcance | [07-DEPLOYMENT-VIEW — Health Checks](./07-DEPLOYMENT-VIEW.md#-health-checks) define el mecanismo objetivo para los 6 contenedores nuevos; el `docker-compose.yml` real hoy en el repositorio corresponde al alcance anterior y sí declara `healthcheck` para `postgres`, pero no para `mcp-tools` ni `mcp-frontend` |

## 🔧 Mantenibilidad

| # | Escenario | Estímulo | Respuesta esperada / Medida | Estado | Evidencia |
|---|-----------|----------|-------------------------------|--------|-----------|
| M1 | Cobertura de tests | Un desarrollador ejecuta la suite de tests de un módulo del nuevo alcance | Cobertura mínima del 80% (Unit 60% / Integration 30% / E2E 10%, según `CLAUDE.md`) | ❌ Pendiente — 0% medido | Ninguno de los siete módulos del nuevo alcance tiene código todavía, y por lo tanto tampoco tests (ver enfoque de testing objetivo por módulo en [08-CROSSCUTTING-CONCEPTS — Testing](./08-CROSSCUTTING-CONCEPTS.md#-testing)); el código heredado (`api/test_integration.py`, `server/test_cv.py`) tampoco declara framework de cobertura |
| M2 | Documentación Arc42 actualizada | Se completa una fase de diseño arquitectónico | Las 12 secciones Arc42 (`docs/01-*` a `docs/12-*`) reflejan el nuevo alcance de portafolio de forma coherente | ✅ Cumple | Este mismo documento y sus 11 hermanos (`docs/01-INTRODUCTION.md` a `docs/12-GLOSSARY.md`) están redactados y actualizados a 2026-08-16 sobre el alcance de cjhirashi-career, cada uno marcando explícitamente qué es diseño objetivo frente a lo ya implementado |
| M3 | Deuda técnica registrada y priorizada | Un desarrollador nuevo necesita saber qué falta y en qué orden atenderlo | Existe un registro explícito de riesgos/deuda con priorización, no solo una lista sin orden | ✅ Cumple | [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md) registra 12 riesgos con probabilidad, impacto, mitigación y un orden de atención recomendado |
| M4 | Separación de responsabilidades en el código | Un desarrollador nuevo lee el código de la API REST del nuevo alcance | Cada capa (`Controllers → Services → Repository → Models`) tiene un límite claro, con siete servicios de dominio de responsabilidad única | ❌ Pendiente — diseño definido, no implementado | Diseño objetivo completo en [05-BUILDING-BLOCK-VIEW — Nivel 2: API REST](./05-BUILDING-BLOCK-VIEW.md#-nivel-2--descomposición-de-la-api-rest); el código real actual (`api/`) implementa el alcance anterior, sin capa de `Services` separada de `Controllers` |

## 🔐 Seguridad

| # | Escenario | Estímulo | Respuesta esperada / Medida | Estado | Evidencia |
|---|-----------|----------|-------------------------------|--------|-----------|
| S1 | Aislamiento entre usuarios | Una consulta o mutación de carrera se ejecuta contra la API REST | Toda consulta filtra por `user_id`; no es posible leer o modificar datos de otro usuario | ⚠️ Diseño lo define, no implementado | [08-CROSSCUTTING-CONCEPTS — Autenticación y Autorización](./08-CROSSCUTTING-CONCEPTS.md#-autenticación-y-autorización): "todo endpoint de gestión de carrera filtra por `user_id`"; las tablas de carrera de [05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md#-base-de-datos-detallada) no existen todavía en PostgreSQL |
| S2 | Expiración de sesión (JWT) | Un cliente presenta un JWT del Admin Panel | El token es rechazado si tiene más de 24 horas de antigüedad | ❌ Pendiente — valor heredado no cumple el objetivo | `api/config.py` define `ACCESS_TOKEN_EXPIRE_DAYS: int = 7` (168 horas), heredado del alcance anterior; [01-INTRODUCTION — Modelo de Seguridad](./01-INTRODUCTION.md#-modelo-de-seguridad) marca este mecanismo como "pendiente de confirmar si se mantiene igual para este nuevo alcance de usuario único" — se registra aquí como objetivo a decidir en el ADR-002 (ver `09-DECISIONS/`) |
| S3 | Restricción de orígenes (CORS) | Un navegador en un origen no autorizado intenta llamar a la API REST | La API rechaza la petición por CORS, con un único conjunto de orígenes válidos por entorno | ⚠️ Parcial — mecanismo presente, configuración mezclada | `api/config.py` (`CORS_ORIGINS_STR`) y `docker-compose.yml` implementan el mecanismo, pero mezclan orígenes de desarrollo (`localhost:3000`) con los de despliegue — mismo patrón de riesgo que en el alcance anterior (ver [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md)) |
| S4 | Cumplimiento OWASP Top 10 | Se audita cualquiera de los tres canales expuestos a Internet (Portal Público, Admin Panel, MCP Server) | Ninguna de las diez categorías OWASP presenta una vulnerabilidad conocida sin mitigar | ❌ Pendiente — sin auditoría realizada | Restricción explícita en [02-ARCHITECTURE-GOALS — Restricciones](./02-ARCHITECTURE-GOALS.md#-restricciones) ("Cumplimiento de prácticas OWASP en todos los canales expuestos a Internet"); no existe todavía un escaneo ni checklist OWASP ejecutado sobre este proyecto |
| S5 | Gestión de secretos | Se audita el repositorio en busca de credenciales expuestas | `SECRET_KEY`, credenciales de PostgreSQL y credenciales de AWS Bedrock no están versionadas en texto plano | ❌ Pendiente — falla hoy | `docker-compose.yml` actual versiona `SECRET_KEY: mcp-secret-key-change-in-production-32chars-min` y `POSTGRES_PASSWORD: mcppass123` en texto plano; [07-DEPLOYMENT-VIEW — Ambiente de Producción](./07-DEPLOYMENT-VIEW.md#-ambiente-de-producción) exige resolverlo vía variables de entorno o gestor de secretos antes de cualquier despliegue |

## 📈 Escalabilidad

| # | Escenario | Estímulo | Respuesta esperada / Medida | Estado | Evidencia |
|---|-----------|----------|-------------------------------|--------|-----------|
| E1 | Escalado horizontal de la API REST | El volumen de tráfico de los tres canales crece más allá de una instancia | La API REST corre en múltiples réplicas sin coordinación adicional, al ser *stateless* respecto a negocio | ⚠️ Diseño lo permite, no implementado ni probado | Objetivo técnico priorizado #4 en [02-ARCHITECTURE-GOALS.md](./02-ARCHITECTURE-GOALS.md#-objetivos-técnicos); la API REST heredada ya usa JWT sin sesión de servidor (patrón *stateless* reutilizable), pero corre como instancia única sin réplicas configuradas |
| E2 | Escalado de PostgreSQL (réplica de lectura) | El volumen de lecturas de los tres dominios de datos satura la instancia única | El sistema soporta un patrón primaria/réplica | ❌ Pendiente, no priorizado | [07-DEPLOYMENT-VIEW — Ambiente de Producción](./07-DEPLOYMENT-VIEW.md#-ambiente-de-producción): "sin réplicas... definidas en este documento — pendiente de diseño, coherente con el alcance de MVP de un único usuario administrador" |
| E3 | Volumen de datos de métricas y eventos | Las tablas `mcp_agent_metrics`, `portal_visits` y `portal_interactions` acumulan registros con el uso normal del sistema | El volumen mensual permanece por debajo de 1 GB (comprimido), sostenido por la política de retención de 90 días | ❌ Pendiente — sin objetivo dimensionado previamente | Es la primera vez que este umbral se fija en la documentación Arc42 del proyecto; [08-CROSSCUTTING-CONCEPTS — Sistema de Métricas](./08-CROSSCUTTING-CONCEPTS.md#-sistema-de-métricas) define una retención de 90 días pero no un límite de tamaño — se registra aquí como candidato a incorporar junto con la política de archivado (ver mitigación en [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md)) |

## 🎨 Usabilidad

| # | Escenario | Estímulo | Respuesta esperada / Medida | Estado | Evidencia |
|---|-----------|----------|-------------------------------|--------|-----------|
| U1 | Eficiencia de tareas frecuentes en el Admin Panel | Carlos Jiménez Hirashi realiza una tarea habitual (registrar una competencia, mover una vacante de estado) | La tarea se completa en 5 clics o menos desde la pantalla de inicio de la sección correspondiente | ❌ Pendiente — sin interfaz que medir | El Admin Panel y sus componentes (`EntityForm`, `VacancyBoard`) son diseño objetivo en [05-BUILDING-BLOCK-VIEW — Admin Panel Detallado](./05-BUILDING-BLOCK-VIEW.md#-admin-panel-detallado), sin implementación ni prueba de usabilidad realizada |
| U2 | Claridad y accionabilidad de las métricas mostradas | Carlos Jiménez Hirashi consulta el Metrics Dashboard para decidir si algo requiere su atención | Cada gráfico responde a una pregunta operativa concreta (¿cuántas solicitudes MCP hubo?, ¿hay errores?, ¿de dónde viene el tráfico?), sin datos sin contexto | ❌ Pendiente — sin dashboard implementado | Diseño objetivo del `McpMetricsPanel` y `PortalTrafficPanel` en [05-BUILDING-BLOCK-VIEW.md](./05-BUILDING-BLOCK-VIEW.md#tabla-de-componentes-react-principales); ningún dato real disponible para evaluar accionabilidad todavía |

## 📊 Resumen de Estado

| Atributo | ✅ Cumple | ⚠️ Parcial | ❌ Pendiente | Total escenarios |
|----------|:---:|:---:|:---:|:---:|
| Rendimiento | 0 | 0 | 4 | 4 |
| Disponibilidad | 0 | 1 | 3 | 4 |
| Mantenibilidad | 2 | 0 | 2 | 4 |
| Seguridad | 0 | 2 | 3 | 5 |
| Escalabilidad | 0 | 1 | 2 | 3 |
| Usabilidad | 0 | 0 | 2 | 2 |
| **Total** | **2** | **4** | **16** | **22** |

**Lectura del panorama**: a diferencia de la revisión anterior de este documento (donde el sistema heredado sí tenía código real que evaluar), este documento evalúa un sistema que **existe únicamente como diseño**. Los dos únicos escenarios que cumplen hoy (M2, M3) son sobre la documentación misma, no sobre el sistema en ejecución — un resultado honesto y esperable para un proyecto en fase de rediseño de alcance (ver estado "diseño en validación" en todos los documentos `01-*` a `08-*`). Los cuatro escenarios parciales (D4, S1, S3, E1) reflejan mecanismos o patrones ya usados en el alcance anterior que son razonablemente reutilizables, pero que no han sido verificados contra las nuevas tablas, canales y componentes descritos en este Arc42. Antes de iniciar la implementación, el Arquitecto de Soluciones debería priorizar cerrar S5 (secretos en texto plano) y S2 (expiración de JWT), por ser los de menor esfuerzo y mayor exposición de seguridad — ver el orden de atención completo en [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md#-orden-de-atención-recomendado).

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [02-ARCHITECTURE-GOALS.md](./02-ARCHITECTURE-GOALS.md) · [06-RUNTIME-VIEW.md](./06-RUNTIME-VIEW.md) · [07-DEPLOYMENT-VIEW.md](./07-DEPLOYMENT-VIEW.md) · [08-CROSSCUTTING-CONCEPTS.md](./08-CROSSCUTTING-CONCEPTS.md) · [11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md) · [CLAUDE.md](../CLAUDE.md)
**Contacto**: Carlos Jiménez Hirashi (cjhirashi@gmail.com)
