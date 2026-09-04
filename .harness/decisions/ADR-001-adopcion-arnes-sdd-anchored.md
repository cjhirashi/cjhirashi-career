---
id: ADR-001
tipo: adr
estado: accepted
fecha: 2026-09-04
---

# ADR-001 · Adopción del arnés SDD Anchored (simplificado) + perfil de arquitectura

## Contexto y planteamiento del problema

`cjhirashi-career` es un monorepo de microservicios en desarrollo asistido por
agentes de IA. Un arnés anterior existió (rama `feat/admin-sections-split-tables`)
pero resultó **sobrecargado** para el tamaño del proyecto (proceso de ~330 líneas,
plan de ~520, 9 bloques de gate, 6 manuales de rol, 10 stubs de agente, ledger
aparte, triada de memoria). El repo se restauró a un commit anterior (8227848) sin
arnés. Hace falta un arnés que dé gobernanza, trazabilidad y anti-drift **sin**
esa ceremonia, y que sea barato de operar en tokens.

## Decisión

1. **Adoptar el arnés SDD Anchored en su versión simplificada** (diseñada en el repo
   `harness`, `docs/model` + `docs/structure`):
   - **3 archivos por feature**: `spec.md` (con el anclaje `covers`/`anchor_commit`/
     `anchor_mode` en su front-matter), `plan.md`, `tasks.md` (con la tabla de
     cobertura que **es** la trazabilidad). `contracts/` sólo si el perfil lo pide.
   - **Método en 1 archivo** (`.harness/method.md`), sin `process/` ni `roles/`.
   - **Memoria en 2 archivos** (`memory/state.md` con las correcciones del usuario
     fijas arriba + `memory/history.md`).
   - **Compuerta ejecutable local** (`.harness/gate/check.sh`), no CI.
   - Estado de cada feature = `estado:` en el front-matter de su `spec.md` (sin
     `feature-ledger.json`).
   - Flujo de 4 fases con **elicitación interactiva** en Fase 1 y **2 gates humanos**.
   - Reglas transversales: **solución de raíz, nunca parche** (Constitución Art. 10);
     **documentación del proyecto sincronizada** (Art. 11); **el agente siempre
     recomienda la mejor alternativa, el usuario decide**.

2. **Registrar el perfil de arquitectura detectado** (Génesis en modo alineación):
   - Estilo de despliegue: **microservicios en monorepo** (api, ai, admin, portfolio,
     mcp) + infraestructura compartida (Postgres, Qdrant, MinIO).
   - **Patrón interno: por capas** (`routes → services → repositories → models` en los
     servicios Python; `components → hooks → services → stores` en los frontends
     React). **No hexagonal.**
   - Sustratos de integración: `rest-http`, `mcp`, `bedrock-llm`, `qdrant-vector`.
   - Topología de agentes: **multi-perfil Bedrock** (perfiles `agent-N`, delegación
     entre perfiles, niveles L1/L2/L3 — ADRs de producto 012/013).
   - Detalle completo: `constitution.md` Art. 2.

## Opciones consideradas

- **Recuperar el arnés anterior tal cual.** Descartada: es el que se juzgó
  sobrecargado; su backlog y varios invariantes (p. ej. `section_catalog` forkeado
  api⇄ai) corresponden a trabajo posterior a 8227848 o revertido.
- **Arnés simplificado desde cero, sin mirar el anterior.** Descartada: perdería
  conocimiento duro ya capturado (hazards de arranque, context-packs de subproyectos,
  lecciones del usuario).
- **Arnés simplificado + reuso selectivo de contenido del anterior.** **Elegida.**

## Consecuencias

- **Buenas:** superficie del arnés mucho menor; arranque de sesión ~120–200 líneas;
  trazabilidad y anti-drift intactos; monitoreo barato gracias al formato fijo de
  Session-End en `history.md`.
- **Coste:** sin lock global por subproyecto (un proyecto de este tamaño con un solo
  operador humano no lo necesita); si el equipo crece, se añade vía un `ADR-` nuevo.
  Sin manuales de rol detallados — el patrón CIV queda como guía opcional en
  `method.md §8`.

## Enlaces

- Método: `.harness/method.md`. Perfil de arquitectura: `.harness/constitution.md` Art. 2.
- Diseño del arnés genérico: repo `harness`, `docs/model/` + `docs/structure/`.
- Arnés anterior (referencia histórica): rama `feat/admin-sections-split-tables`.
