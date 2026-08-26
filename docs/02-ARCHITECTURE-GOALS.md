# Metas y Restricciones Arquitectónicas - cjhirashi-career

**METAS ARQUITECTÓNICAS**

[![Document Type](https://img.shields.io/badge/type-architecture-blue)]()
[![Audience](https://img.shields.io/badge/audiencia-arquitectos%20%7C%20developers-informational)]()
[![Estado](https://img.shields.io/badge/estado-diseño%20en%20validación-yellow)]()

---

**Última actualización**: 2026-08-16
**Resumen rápido**: 3 objetivos de negocio · 6 objetivos técnicos priorizados · 5 restricciones no negociables · 5 convenciones de equipo — todos heredados del framework de calidad definido en `CLAUDE.md`

---

## 📋 Tabla de Contenidos

- [Propósito de este Documento](#-propósito-de-este-documento)
- [Objetivos de Negocio](#-objetivos-de-negocio)
- [Objetivos Técnicos](#-objetivos-técnicos)
- [Restricciones](#-restricciones)
- [Convenciones de Equipo](#-convenciones-de-equipo)
- [Relación con Otras Secciones](#-relación-con-otras-secciones)

---

## 🎯 Propósito de este Documento

Esta sección responde a una pregunta distinta de la que responde [01-INTRODUCTION.md](./01-INTRODUCTION.md): mientras la introducción describe **qué es** el sistema y **cómo está compuesto**, esta sección fija **qué debe lograrse** y **qué no es negociable** al construirlo. Toda decisión arquitectónica posterior — la elección de un patrón, un ADR, la forma de un componente en `05-BUILDING-BLOCK-VIEW.md` — debe poder justificarse contra alguno de los objetivos o restricciones aquí listados.

Los objetivos y restricciones de este documento no se inventan de cero: se derivan directamente del alcance descrito en la introducción (tres canales convergentes, usuario único administrador, agentes de IA externos) y del framework de calidad ya vigente para el proyecto, definido en `CLAUDE.md`.

## 🎯 Objetivos de Negocio

Estos objetivos existen para justificar por qué el sistema se construye — son la razón de negocio, no la solución técnica.

| # | Objetivo | Descripción |
|---|----------|--------------|
| 1 | **Portafolio profesional del usuario** | Ofrecer a Carlos Jiménez Hirashi una presencia profesional pública, curada y siempre actualizada, que reemplace la necesidad de mantener manualmente un sitio estático — cualquier avance en su carrera (nuevo proyecto, logro, publicación) debe poder reflejarse en el Portal Público sin trabajo de mantenimiento web adicional. |
| 2 | **Gestión centralizada de carrera** | Concentrar en un único sistema toda la información dispersa de una búsqueda o gestión de carrera profesional — identidad, competencias, evidencia, vacantes, contactos y preparación de entrevistas — de forma que Carlos Jiménez Hirashi tenga una sola fuente de verdad en lugar de documentos, hojas de cálculo y notas sueltas. |
| 3 | **Acceso para agentes IA externos** | Permitir que un agente de inteligencia artificial externo (por ejemplo Claude u otro cliente MCP) opere autónomamente sobre esa misma gestión de carrera — leyendo contexto y proponiendo o registrando actualizaciones — sin requerir la presencia simultánea de Carlos Jiménez Hirashi frente al Admin Panel. |

## ⚙️ Objetivos Técnicos

A diferencia de los objetivos de negocio, estos son atributos de calidad medibles o verificables sobre la arquitectura. Se listan en el orden de prioridad acordado por el Arquitecto de Soluciones: ante un conflicto entre dos objetivos, el de menor número gana.

| Prioridad | Atributo de calidad | Objetivo | Motivo de la prioridad |
|-----------|---------------------|----------|--------------------------|
| 1 | **Independencia de canales** | Portal Público, Admin Panel y MCP Server deben operar como tres puntos de entrada completamente autónomos entre sí, convergiendo únicamente en la API REST y la base de datos — ninguno depende de que otro esté activo. | Es la restricción estructural de la que dependen todos los demás objetivos: si un canal falla o está inactivo, los otros dos deben seguir funcionando sin degradación. |
| 2 | **SPA dinámico y operativo** | El Admin Panel debe comportarse como una aplicación de una sola página completamente funcional — CRUD dinámico sobre todas las entidades de carrera, panel de métricas y chat con Agent Bedrock — sin recargas de página ni flujos rotos entre secciones. | Es la superficie de trabajo diaria de Carlos Jiménez Hirashi; cualquier fricción de uso afecta directamente el objetivo de negocio de gestión centralizada. |
| 3 | **Métricas en tiempo real** | El Admin Panel debe exponer visibilidad casi inmediata sobre el uso del MCP Agent, el tráfico del Portal Público, el tracking de visitantes y los eventos de auditoría del sistema. | Sin observabilidad, el usuario administrador no puede confiar en que los agentes externos (canal de mayor autonomía) están operando correctamente. |
| 4 | **Escalabilidad horizontal de la API** | La API REST, como único punto de convergencia de los tres canales, debe poder escalar agregando instancias sin cambios de diseño, dado que concentra la carga de los tres canales simultáneamente. | Es el componente de mayor riesgo de cuello de botella al ser el único orquestador del sistema. |
| 5 | **Aislamiento de datos por usuario** | Aunque el sistema tiene un único usuario administrador hoy, el modelo de datos y las reglas de acceso deben mantener una separación clara entre datos privados de gestión de carrera y datos publicables del Portal Público. | Previene que información de carrera aún no curada (por ejemplo, una vacante en negociación) se filtre accidentalmente al canal público. |
| 6 | **Autenticación y autorización consistentes** | Cada canal debe implementar un mecanismo de control de acceso proporcional a su nivel de exposición y autonomía — sin autenticación para lectura pública, autenticación completa para el Admin Panel, y un mecanismo propio e independiente para el MCP Server. | El MCP Server, al operar sin supervisión humana en tiempo real, concentra el mayor riesgo de autorización del sistema (ver pregunta abierta correspondiente en `01-INTRODUCTION.md`). |

## 🚧 Restricciones

Estas restricciones son decisiones ya tomadas fuera de discusión para el alcance actual — no se reevalúan salvo que cambien las condiciones que las originaron.

| Tipo | Restricción | Justificación |
|------|-------------|----------------|
| **Técnica** | Stack fijo: React (frontends) + FastAPI (API REST) + PostgreSQL (persistencia) | Continuidad con la base técnica heredada del proyecto previo (API REST, PostgreSQL) y decisión explícita del Arquitecto de Soluciones documentada en `CLAUDE.md`. |
| **Infraestructura** | Despliegue en contenedores Docker sobre la red bridge externa `network-cjhirashi-srv` | El sistema comparte infraestructura de hosting (`cjhirashi-srv`) con otros proyectos; la red externa es el mecanismo de integración con el proxy/reverse-proxy existente. |
| **Calidad** | Cobertura mínima de tests del 80% por módulo | Estándar de calidad obligatorio definido en el framework de `CLAUDE.md`, validado por el QA Engineer antes de cualquier merge. |
| **Interoperabilidad** | El MCP Server debe implementar el protocolo Model Context Protocol (MCP) sin desviaciones | Es el contrato de interfaz con el que operan los agentes de IA externos (Claude u otros clientes compatibles); una implementación no conforme rompe la compatibilidad con ese ecosistema. |
| **Seguridad** | Cumplimiento de prácticas OWASP en todos los canales expuestos a Internet (Portal Público, Admin Panel, MCP Server) | Los tres canales de entrada son alcanzables desde fuera de la red interna; el cumplimiento OWASP es la línea base de seguridad exigida por el framework de calidad del proyecto. |

## 📐 Convenciones de Equipo

Convenciones operativas que todo agente del equipo (los 5 agentes globales definidos en `CLAUDE.md` y los especialistas de módulo) debe seguir de forma transversal, independientemente del canal o módulo en el que trabaje.

| Convención | Descripción | Responsable principal |
|------------|-------------|------------------------|
| **Documentación Arc42 + ADRs** | Toda decisión arquitectónica relevante se documenta en la estructura `docs/` (Arc42) y, cuando corresponde, se formaliza como Architecture Decision Record en `docs/09-DECISIONS/` | Documentador, bajo directiva del Arquitecto de Soluciones |
| **SOLID + Clean Code** | Todo módulo de código sigue los cinco principios SOLID y prácticas de Clean Code, incluyendo Domain-Driven Design para lógica de negocio compleja | Especialista de módulo, validado por Code Quality Guardian |
| **Conventional Commits** | Todo commit describe su cambio siguiendo el formato Conventional Commits, habilitando changelogs generables y un historial legible | Git Especialista |
| **Code review obligatorio** | Ningún cambio se integra a `main` sin revisión de pares contra un checklist de calidad (SOLID, Clean Code, cobertura de tests) | Code Quality Guardian |
| **CI/CD con gates de calidad** | El pipeline de build, tests, análisis de calidad, escaneo de seguridad y despliegue se ejecuta de forma obligatoria antes de cualquier merge a `main` | Experto Docker (pipeline) + QA Engineer (validación de cobertura) |

## 🔗 Relación con Otras Secciones

- **[01-INTRODUCTION.md](./01-INTRODUCTION.md)**: describe el sistema y sus componentes; este documento define qué debe lograr ese sistema y bajo qué restricciones.
- **[03-STAKEHOLDERS.md](./03-STAKEHOLDERS.md)**: identifica quién se beneficia de cada objetivo de negocio listado aquí.
- **[04-SOLUTION-STRATEGY.md](./04-SOLUTION-STRATEGY.md)**: explica las decisiones de alto nivel adoptadas para satisfacer estos objetivos técnicos dentro de estas restricciones.
- **`docs/09-DECISIONS/`**: contendrá los ADRs formales que resuelvan las preguntas de validación abiertas en `01-INTRODUCTION.md`, siempre trazables a uno o más de los objetivos técnicos priorizados en este documento.

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [03-STAKEHOLDERS.md](./03-STAKEHOLDERS.md) · [04-SOLUTION-STRATEGY.md](./04-SOLUTION-STRATEGY.md) · [CLAUDE.md](../CLAUDE.md)
**Contacto**: Carlos Jiménez Hirashi (cjhirashi@gmail.com)
