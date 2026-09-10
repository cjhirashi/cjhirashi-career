---
id: ADR-003
tipo: adr
estado: accepted
fecha: 2026-09-10
---

# ADR-003 · Especialista de UX/UI en el arnés

## Contexto y planteamiento del problema

El proyecto tiene dos frontends React/Vite (`cjhirashi-career-admin`,
`cjhirashi-career-portfolio`). Hasta ahora la calidad de UX/UI dependía del criterio
del `implementador` de turno, sin un estándar explícito ni una revisión dedicada — se
priorizaba "que funcione" sobre "que esté bien diseñado y sea profesional".

`.claude/agents/README.md` fija que un especialista nuevo se añade **vía un `ADR-`**
cuando el dominio lo justifica. El dominio UX/UI lo justifica: es transversal a toda
feature de interfaz y necesita criterio de diseño, no solo de implementación.

## Decisión

Se añade el especialista **`experto-ux-ui`** a `.claude/agents/`:

- **Delegable** por el `orquestador`/`autor-de-spec`/`arquitecto` en cualquier feature
  que toque interfaz de un frontend.
- **Interviene en Fase 1/2:** aporta flujos de usuario, estados por vista (vacío,
  cargando, error, sin permiso, muchos datos), componentes a reutilizar y `RF-` de UX
  medibles. Una spec de frontend no está lista para el Gate 1 sin esta sección.
- **Interviene en Fase 4:** revisa la UI construida contra un estándar profesional
  (jerarquía visual, espaciado, tipografía, contraste **WCAG AA**, consistencia de
  componentes, accesibilidad por teclado/ARIA, responsive, microcopy, movimiento con
  propósito) **antes** de que el `revisor` cierre. Entrega un informe priorizado
  (bloqueante / debería / nice-to-have), no un parche.
- **No escribe el código de producción del frontend** (eso sigue siendo del
  `implementador`). Diseña y revisa. No aprueba nada `verified`.

Se añade también a `.harness/constitution.md` Art. 8 una cláusula: **toda feature que
toque interfaz de un frontend pasa por la revisión de UX/UI** (delegable a este
especialista) antes de `verified`.

## Consecuencias

- **Buenas:** los frontends tienen un estándar de UX/UI explícito y una revisión
  dedicada; la accesibilidad deja de ser opcional.
- **Coste:** una feature de frontend gana un paso de revisión (rápido si la spec ya
  incluyó la sección de UX). Es un especialista opcional — features sin interfaz no lo
  tocan.

## Enlaces

- Agente: `.claude/agents/experto-ux-ui.md`.
- Afecta a: `.harness/constitution.md` Art. 8, `.claude/agents/README.md`, `AGENTS.md`.
- Relacionado: `ADR-001` (adopción del arnés).
