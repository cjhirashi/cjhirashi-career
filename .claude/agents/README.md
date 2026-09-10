# .claude/agents/ — binding de Claude Code

Estos archivos son el **binding del arnés a Claude Code**: subagentes que el
`orquestador` invoca. El **manual operativo** de cada rol NO vive aquí — vive en
`.harness/method.md §8`. Cada stub es ~15 líneas: `frontmatter` (`name`,
`description`, `tools`, `model`) + arranque + reglas duras + convención de salida
(una línea + referencia a archivo).

## Conjunto base (mapea 1:1 a `method.md §8`)

| Agente | Rol | model |
|---|---|---|
| `orquestador` | Coordinador — clasifica, sostiene las puertas humanas, delega, cierre | sonnet |
| `autor-de-spec` | Fase 1 · elicitación interactiva → `spec.md` | sonnet |
| `arquitecto` | Fase 2 · `plan.md` conforme al patrón + `covers` | sonnet |
| `implementador` | Fase 4 · TDD, una tarea a la vez | sonnet |
| `revisor` | Verificador adversarial · corre el gate, traza `RF-↔test` | sonnet |
| `explorador` | Búsqueda read-only acotada antes de speccar | haiku |

`revisor` nunca es más débil que `implementador` (lección: implementador en haiku
fabricó evidencia).

## Especialistas de dominio (opcionales)

**Destinos de delegación acotada** del `orquestador`/`autor-de-spec`/`arquitecto`. Se
añaden **vía un `ADR-`**.

| Especialista | Qué hace | ADR | model |
|---|---|---|---|
| `experto-ux-ui` | Diseña y revisa la UX/UI de los frontends (`admin`, `portfolio`). Aporta flujos y estados en Fase 1/2; revisa la UI contra un estándar profesional (contraste WCAG AA, consistencia de componentes, accesibilidad, responsive, microcopy) en Fase 4, antes de que cierre el `revisor`. **No escribe código de producción.** | `ADR-003` | sonnet |
