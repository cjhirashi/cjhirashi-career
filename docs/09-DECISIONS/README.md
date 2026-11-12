# Registro de Decisiones Arquitectónicas (ADR) - cjhirashi-career

**ARCHITECTURE DECISION RECORDS** (arc42, sección 9)

**Última actualización**: 2026-11-05
**Resumen**: 25 ADR de producto (008 a 032), todos aceptados salvo el 009 (deprecado por el 012). Las decisiones **del arnés** viven en `.harness/decisions/`, no aquí.

---

## Cómo leer este documento

Este documento es el marco y el índice de los ADR del producto, uno por archivo en esta carpeta. Las decisiones estructurales de más alto nivel (dos canales hacia una API, SPA para el Admin, PostgreSQL centralizado, API como orquestador, Agent Bedrock como capacidad interna) están narradas en [04-SOLUTION-STRATEGY.md](../04-SOLUTION-STRATEGY.md); no se formalizaron como ADR 001 a 007, por eso la numeración efectiva empieza en 008.

Un ADR aceptado no se edita: si la decisión cambia, un ADR nuevo la revisa o la deprecia. La única edición permitida es la línea de estado, para enlazar al ADR que lo revisa.

## 📌 Qué es un ADR

Un **Architecture Decision Record (ADR)** es un documento corto e inmutable que registra una decisión arquitectónica importante: qué se decidió, **por qué** (no solo qué), qué alternativas se consideraron y qué consecuencias trae. Su propósito no es documentar el sistema — para eso están las secciones 1 a 8 de este Arc42 — sino preservar el razonamiento detrás de una decisión, para que alguien en el futuro (incluido uno mismo) entienda por qué el sistema es como es y no de otra forma.

## 🚦 Cuándo Crear (y Cuándo No) un ADR

**Crear un ADR cuando:**
- La decisión es arquitectónicamente importante (afecta la estructura, las dependencias o las restricciones del sistema).
- Se consideraron alternativas significativamente distintas antes de decidir.
- El impacto se extiende al mediano o largo plazo del proyecto.
- Es razonable esperar que alguien en el futuro se pregunte "¿por qué hicieron esto así?".

**No crear un ADR para:**
- Decisiones tácticas pequeñas (nombre de una variable, estructura interna de una función).
- Cambios menores de código sin impacto estructural.
- Corrección de bugs rutinaria.

## 📐 Template Estándar

Copiar el siguiente contenido como `ADR-XXX-título-descriptivo.md` dentro de esta misma carpeta (`docs/09-DECISIONS/`):

```markdown
# ADR-[NÚMERO]: [Título Descriptivo]

## Estado

[Propuesto | Aceptado | Deprecado | Rechazado]

## Contexto

[Explicar la situación que requería una decisión. Qué problema teníamos. Por qué fue importante decidir esto. Listar alternativas consideradas brevemente.]

## Decisión

[QUÉ se decidió, de forma clara y concisa]

### Por Qué

[El POR QUÉ es lo importante — explicar las razones detrás de la decisión, por qué fue mejor que las alternativas]

- Razón 1: [Explicación]
- Razón 2: [Explicación]

## Consecuencias

### ✅ Positivas
- [Beneficio 1]
- [Beneficio 2]

### ⚠️ Negativas
- [Costo/Desventaja 1]

### 🤷 Neutras
- [Aspecto que no es ni bueno ni malo]

## Alternativas Consideradas

### Alternativa 1: [Nombre]
[Descripción breve]
- ✅ Pro: [Ventaja]
- ❌ Contra: [Por qué se rechazó]

### Alternativa 2 (ELEGIDA): [Nombre]
[Descripción breve]
- ✅ Pro: [Ventaja principal]

## Referencias

- [Link a PR, commit o documento relacionado]

## Implicaciones

- [ ] [Acción que debe hacerse como consecuencia de esta decisión]

## Seguimiento

[Si esta decisión lleva a otras decisiones, mencionarlas aquí. Ej: "ADR-008 describe cómo se implementa esto en detalle"]

---

**Creado por**: [Nombre]
**Aprobado por**: [Nombre del revisor]
**Fecha de creación**: YYYY-MM-DD
**Última revisión**: YYYY-MM-DD
**Estado de vigencia**: [Vigente | Revisar próximo trimestre | Pendiente implementación]
```

## Registro de decisiones

| # | Decisión | Estado |
|---|---|---|
| 008 | [Bedrock Harness local (Converse API)](./008-bedrock-harness-local.md) | ⛔ Retirado por ADR-033 |
| 009 | [Multi-agente — dos chats y delegación](./009-bedrock-multi-agent-profiles.md) | ⛔ Deprecado |
| 010 | [Agentes agent_pdf_design y agent_visual_design](./010-bedrock-visual-pdf-agents.md) | ⛔ Retirado por ADR-033 |
| 011 | [Descubrimiento de vacantes por adaptadores (sin scraping)](./011-job-discovery-adapters.md) | ⛔ Retirado por ADR-034 |
| 012 | [Jerarquía de agentes en 3 niveles](./012-bedrock-three-level-agents.md) | ⛔ Retirado por ADR-033 |
| 013 | [L3 consulta web y L3 GitHub (solo lectura)](./013-l3-web-and-github-agents.md) | ⛔ Retirado por ADR-033 |
| 014 | [Cuatro módulos de aplicación](./014-four-application-modules.md) | ✅ Aceptado (revisado parcialmente) |
| 015 | [Tareas de primer nivel y ejecución autónoma de agentes](./015-scheduled-agent-tasks.md) | ⛔ Retirado por ADR-033 |
| 016 | [Subtareas, orquestación por turno y notificaciones al usuario](./016-task-subtasks-orchestration.md) | ⛔ Retirado por ADR-033 |
| 017 | [L2 `agent_settings` — Configuración (catálogo de agentes, secciones del Admin, prompts globales)](./017-l2-agent-settings.md) | ⛔ Retirado por ADR-033 |
| 018 | [Registro centralizado de fallas del sistema (`error_reports`)](./018-error-reports-registry.md) | ✅ Aceptado |
| 019 | [Prompt caching de Bedrock + proyección de campos y truncado por campo](./019-bedrock-prompt-caching.md) | ⛔ Retirado por ADR-033 |
| 020 | [Plantilla compartida para las secciones de tabla del Admin](./020-admin-section-templates.md) | ⛔ Retirado por ADR-033 |
| 021 | [PK sintético `sec-N` para las secciones del Admin (`system_name` como nombre legible)](./021-admin-sections-synthetic-pk.md) | ⛔ Retirado por ADR-033 |
| 022 | [División del L2 `agent_settings` — Configuración vs. Incidencias/Bitácora](./022-l2-split-configuration-vs-incidents.md) | ⛔ Retirado por ADR-033 |
| 023 | [Retirar el MCP Server del alcance activo](./023-retirar-mcp-server.md) | ✅ Aceptado |
| 024 | [El sidebar contextual del Admin lo gobierna la sección](./024-sidebar-contextual-por-seccion.md) | ⛔ Retirado por ADR-033 |
| 025 | [Migrar la generación de imágenes de Titan a Stability Stable Image Core](./025-migrar-generacion-imagenes-a-stability.md) | ⛔ Retirado por ADR-033 |
| 026 | [Configuración de agentes desde la App (metodologías y herramientas)](./026-configuracion-agentes-app.md) | ⛔ Retirado por ADR-033 |
| 027 | [Herramientas y metodologías por sección (agentes L2)](./027-herramientas-metodologias-por-seccion.md) | ⛔ Retirado por ADR-033 |
| 028 | [Contraste de los tokens semánticos de texto del Admin (tema claro)](./028-contraste-tokens-semanticos-admin.md) | ✅ Aceptado |
| 029 | [Harness de agentes fuera de la API (`cjhirashi-career-ai`) y sin indexación](./029-harness-agentes-fuera-de-api.md) | ⛔ Retirado por ADR-033 |
| 030 | [Documentación de proyectos en 3 campos markdown](./030-proyectos-tres-campos-markdown.md) | ✅ Aceptado |
| 031 | [Embeber HTML e imágenes de Synapse en las fichas](./031-embeber-html-de-synapse-en-fichas.md) | ✅ Aceptado |
| 032 | [Agentes externos por la API; el subsistema Bedrock queda fuera de operación](./032-agentes-externos-y-bedrock-fuera-de-operacion.md) | ✅ Aceptado |
| 033 | [Se retira el subsistema Bedrock y el catálogo de agentes](./033-retiro-del-subsistema-bedrock.md) | ✅ Aceptado |
| 034 | [Se retira el descubrimiento de vacantes](./034-retiro-del-descubrimiento-de-vacantes.md) | ✅ Aceptado |

**Revisiones cruzadas vigentes**: ADR-009 deprecado por ADR-012; ADR-014 revisado parcialmente por ADR-023 (MCP retirado) y por ADR-029 (harness fuera de la API); ADR-008 y ADR-025 revisados parcialmente por ADR-029; ADR-026 parcialmente superado por ADR-027 para los agentes L2.

**Estado de ADR-029**: sin efecto; el ADR-033 (2026-11-11) retiró el subsistema Bedrock y los agentes de IA son externos.

## 🆕 Cómo Crear un Nuevo ADR

1. Confirmar que la decisión cumple los criterios de la sección [Cuándo Crear un ADR](#-cuándo-crear-y-cuándo-no-un-adr).
2. Copiar el [Template Estándar](#-template-estándar) a un archivo nuevo: `ADR-XXX-título-descriptivo.md`, dentro de `docs/09-DECISIONS/`.
3. Usar el siguiente número secuencial disponible — nunca reutilizar un número, incluso si un ADR anterior fue rechazado.
4. Redactar enfatizando el **por qué**, no el qué — el qué ya suele estar documentado en las secciones 1-8 de este Arc42.
5. Agregar la fila correspondiente a la tabla de [Registro de Decisiones](#-registro-de-decisiones) de este README, con el estado real (`Propuesto`, `Aceptado`, etc.).
6. Si el ADR reemplaza una decisión ya documentada en [04-SOLUTION-STRATEGY.md](../04-SOLUTION-STRATEGY.md), actualizar ese documento para enlazar al ADR en vez de repetir la justificación.

## 🔒 Inmutabilidad y Depreciación

- **Un ADR aceptado no se edita.** Si la decisión cambia, se crea un **nuevo ADR** con el siguiente número secuencial que referencia y deprecia al anterior (campo `Seguimiento` del template).
- El ADR depreciado **permanece en el repositorio** con su estado actualizado a `Deprecado` y una referencia al ADR que lo reemplaza — no se elimina, porque sigue explicando por qué se tomó esa decisión en su momento.
- La numeración es secuencial y global para todo el proyecto — no se reinicia por categoría ni por módulo, y no se reutiliza aunque el rediseño de alcance haya dejado sin ADRs previos que continuar.

---

**Relacionado**: [01-INTRODUCTION.md](../01-INTRODUCTION.md) · [02-ARCHITECTURE-GOALS.md](../02-ARCHITECTURE-GOALS.md) · [04-SOLUTION-STRATEGY.md](../04-SOLUTION-STRATEGY.md) · [10-QUALITY-SCENARIOS.md](../10-QUALITY-SCENARIOS.md) · [11-TECHNICAL-RISKS.md](../11-TECHNICAL-RISKS.md) · [CLAUDE.md](../../CLAUDE.md)
**Contacto**: Carlos Jiménez Hirashi (cjhirashi@gmail.com)
