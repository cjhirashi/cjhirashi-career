# Usuarios, Roles y Expectativas - cjhirashi-career

**STAKEHOLDERS DEL PROYECTO**

[![Document Type](https://img.shields.io/badge/type-architecture-blue)]()
[![Audience](https://img.shields.io/badge/audiencia-arquitectos%20%7C%20developers-informational)]()
[![Estado](https://img.shields.io/badge/estado-diseño%20en%20validación-yellow)]()

---

**Última actualización**: 2026-08-16
**Resumen rápido**: 3 grupos de usuarios finales (uno humano, uno anónimo, uno de agentes IA) · equipo de 5 agentes globales + especialistas de módulo · 2 stakeholders de infraestructura — cada uno con necesidades y canales de comunicación distintos

---

## 📋 Tabla de Contenidos

- [Propósito de este Documento](#-propósito-de-este-documento)
- [Usuarios Finales](#-usuarios-finales)
- [Equipo de Desarrollo](#-equipo-de-desarrollo)
- [Stakeholders de Infraestructura](#-stakeholders-de-infraestructura)
- [Matriz de Prioridades](#-matriz-de-prioridades)
- [Comunicación y Feedback](#-comunicación-y-feedback)

---

## 🎯 Propósito de este Documento

Esta sección identifica **quién interactúa con el sistema y con el proyecto**, qué necesita cada uno y qué espera recibir. Es la contraparte humana de `02-ARCHITECTURE-GOALS.md`: los objetivos de negocio existen para satisfacer a alguno de los stakeholders listados aquí, y los objetivos técnicos existen para que esa satisfacción sea sostenible en el tiempo.

Se distinguen tres categorías, en orden de cercanía al sistema en ejecución: **usuarios finales** (interactúan con el sistema ya construido), **equipo de desarrollo** (construyen y mantienen el sistema, según los roles definidos en `CLAUDE.md`) y **stakeholders de infraestructura** (sostienen el entorno donde el sistema corre, sin interactuar con su funcionalidad de negocio).

## 👤 Usuarios Finales

| Stakeholder | Canal de interacción | Qué necesita | Qué espera |
|-------------|------------------------|----------------|--------------|
| **Carlos Jiménez Hirashi** — gestor de carrera | Admin Panel (8002), autenticado | Un lugar único donde registrar y mantener actualizada toda su información de carrera profesional (identidad, competencias, evidencia, vacantes, contactos, entrevistas), con la opción de delegar tareas de redacción o análisis a Agent Bedrock cuando lo prefiera | Que el panel sea rápido, dinámico y confiable; que ningún dato se pierda entre la gestión manual y la asistida por IA; que las métricas del sistema (uso del MCP Agent, tráfico del portal, auditoría) le den visibilidad real sobre lo que ocurre incluso cuando no está usando el panel |
| **Visitantes anónimos** — lectores del portafolio | Portal Público (8003), sin autenticación | Conocer el perfil profesional de Carlos Jiménez Hirashi (About, Proyectos, Blog, Contacto) de forma rápida y sin fricción | Contenido siempre actualizado y coherente con la realidad profesional actual del usuario, sin necesidad de crear cuenta ni de saber que existe un Admin Panel detrás |
| **Agentes de IA externos** — operadores vía MCP | MCP Server (8004), con autenticación propia del canal | Un contrato de herramientas MCP estable y completo que les permita leer y escribir el mismo contexto de carrera que gestiona Carlos Jiménez Hirashi manualmente, sin depender de que el Admin Panel esté abierto | Respuestas predecibles, herramientas bien definidas, y un canal que opere de forma autónoma incluso sin supervisión humana simultánea (ver preguntas de autorización abiertas en `01-INTRODUCTION.md`) |

## 🛠️ Equipo de Desarrollo

El equipo trabaja bajo el modelo de 5 agentes globales definido en `CLAUDE.md`, cada uno con una responsabilidad transversal a todos los módulos, más especialistas dedicados a cada módulo específico.

| Rol | Qué necesita | Qué espera |
|-----|----------------|--------------|
| **Arquitecto de Soluciones** (Carlos, en este rol) | Visibilidad completa de la arquitectura y trazabilidad de cada decisión, para poder diseñar sin ambigüedad y coordinar al resto del equipo | Que cada especialista respete el diseño acordado y escale las desviaciones en lugar de improvisarlas |
| **Experto Docker** (global) | Definición clara de los 4 módulos y la infra (puertos y dependencias), para poder construir y mantener `docker-compose.yml` y el pipeline de CI/CD | Que cualquier cambio de topología (nuevo servicio, cambio de puerto) se le comunique antes de implementarse en código |
| **Documentador** (global, este agente) | Directivas explícitas del Arquitecto sobre qué documentar y protocolos/templates centralizados para no improvisar formato | Que la arquitectura no cambie sin que se le informe, para evitar que la documentación quede desincronizada del diseño real |
| **QA Engineer** (global) | Criterios de calidad claros (80% de cobertura mínima) y visibilidad de qué módulos están en desarrollo activo | Que cada especialista entregue unit tests de su módulo antes de solicitar validación de cobertura |
| **Code Quality Guardian** (global) | Acceso a todo el código para ejecutar revisiones y validar SOLID, Clean Code y seguridad | Que ningún cambio se integre a `main` sin pasar por su revisión |
| **Git Especialista** (global) | Convención de commits (Conventional Commits) y estrategia de ramas acordada | Que los especialistas de módulo sigan la convención de commits sin necesidad de corrección posterior |
| **Especialistas de módulo** (Portal, Admin Panel, API, MCP Server) | Especificación de su módulo dentro de la arquitectura general, y las interfaces exactas con los módulos vecinos | Que la arquitectura general no cambie sus interfaces sin previo aviso, dado que su trabajo depende de contratos estables con la API REST |

## 🏗️ Stakeholders de Infraestructura

Estos stakeholders no interactúan con la funcionalidad de negocio del sistema, pero su disponibilidad y sus reglas condicionan cómo se despliega y opera.

| Stakeholder | Qué necesita | Qué espera |
|-------------|----------------|--------------|
| **Administrador de `cjhirashi-srv`** | Conocer con anticipación qué puertos y qué nombre de red Docker (`network-cjhirashi-srv`) requiere el proyecto, para configurar correctamente el proxy/reverse-proxy del servidor compartido | Que solo los tres canales realmente públicos (Portal 8003, Admin 8002, MCP 8004) se expongan, y que ningún componente interno (API REST, PostgreSQL) intente publicarse directamente |
| **DevOps (CI/CD)** | Definición de los gates de calidad obligatorios (build, tests, cobertura, seguridad, despliegue) para poder automatizarlos en el pipeline | Que el pipeline sea la única vía de despliegue a producción, sin despliegues manuales que salten los gates de calidad |

## 📊 Matriz de Prioridades

Cuando dos necesidades de stakeholders entran en conflicto (por ejemplo, velocidad de entrega para Carlos Jiménez Hirashi vs. cobertura de tests exigida por QA Engineer), esta matriz define quién prioriza sobre quién y en qué momento del ciclo de vida del proyecto.

| Momento | Stakeholder prioritario | Impacto de no priorizarlo |
|---------|--------------------------|------------------------------|
| **Diseño de arquitectura** | Arquitecto de Soluciones | Sin una arquitectura validada, los especialistas de módulo construyen sobre supuestos distintos y generan incompatibilidades entre canales |
| **Definición de qué se documenta** | Arquitecto de Soluciones (el Documentador ejecuta, no decide contenido) | La documentación se desalinea del diseño real, perdiendo su valor como fuente de verdad |
| **Aprobación de merge a `main`** | Code Quality Guardian (bloqueante) + QA Engineer (cobertura) | Código sin revisión o sin cobertura mínima introduce deuda técnica y riesgo de regresión en un sistema con tres canales de escritura independientes |
| **Uso diario del Admin Panel** | Carlos Jiménez Hirashi | Un panel poco usable rompe el objetivo de negocio de gestión centralizada de carrera (ver `02-ARCHITECTURE-GOALS.md`) |
| **Disponibilidad del Portal Público** | Visitantes anónimos | Es el único stakeholder sin ninguna vía de reporte directo de fallos — su experiencia depende enteramente de que el sistema funcione sin intervención |
| **Autorización de operaciones del MCP Server** | Carlos Jiménez Hirashi (como dueño de los datos) | Un agente externo mal configurado o sin límites de autorización claros puede modificar datos de carrera sin supervisión humana en tiempo real — es el escenario de mayor riesgo del sistema, aún abierto en `01-INTRODUCTION.md` |
| **Configuración de red e infraestructura compartida** | Administrador de `cjhirashi-srv` | Un cambio de puertos o de red no coordinado con este stakeholder puede romper el proxy compartido con otros proyectos del servidor |

## 💬 Comunicación y Feedback

| Stakeholder | Canal de comunicación | Frecuencia |
|-------------|--------------------------|------------|
| Carlos Jiménez Hirashi (gestor de carrera) | Uso directo del Admin Panel; feedback verbal/directo al Arquitecto de Soluciones (mismo rol) | Continua, en cada sesión de uso |
| Visitantes anónimos | Sin canal directo — su comportamiento se observa indirectamente mediante el tracking de visitantes registrado en las métricas del Admin Panel | Pasiva, vía métricas agregadas |
| Agentes de IA externos | Sin canal humano — su actividad se observa mediante las métricas de MCP Agent y el registro de auditoría en el Admin Panel | Pasiva, vía métricas y auditoría |
| Equipo de desarrollo (5 agentes globales + especialistas) | Directivas del Arquitecto de Soluciones documentadas en `CLAUDE.md`; coordinación por commit, PR y documentación Arc42/ADR | Por cada entregable o cambio arquitectónico |
| Administrador de `cjhirashi-srv` | Comunicación directa antes de cualquier cambio de puertos, red o exposición de un nuevo canal | Puntual, ante cambios de infraestructura |
| DevOps (CI/CD) | Definición de gates de calidad en el pipeline, coordinada con Experto Docker y QA Engineer | Puntual, al configurar o modificar el pipeline |

---

**Relacionado**: [01-INTRODUCTION.md](./01-INTRODUCTION.md) · [02-ARCHITECTURE-GOALS.md](./02-ARCHITECTURE-GOALS.md) · [04-SOLUTION-STRATEGY.md](./04-SOLUTION-STRATEGY.md) · [CLAUDE.md](../CLAUDE.md)
**Contacto**: Carlos Jiménez Hirashi (cjhirashi@gmail.com)
