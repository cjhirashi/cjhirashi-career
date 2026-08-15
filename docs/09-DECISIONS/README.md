# Architecture Decision Records (ADRs)

Registro de decisiones arquitectónicas tomadas durante el desarrollo del proyecto MCP Tools Server.

Cada ADR documenta:
- **Decisión**: Qué se decidió
- **Contexto**: Por qué fue necesario decidir
- **Alternativas**: Opciones consideradas
- **Consecuencias**: Impacto de la decisión
- **Fecha**: Cuándo se tomó

## ADRs del Proyecto

### Decisiones Registradas

| # | Decisión | Estado |
|---|----------|--------|
| 001 | Docker architecture + 5 independent containers | ✅ Aprobada (2026-08-15) |
| 002 | PostgreSQL como base de datos central | ✅ Aprobada (2026-08-15) |
| 003 | FastAPI para API REST con JWT | ✅ Aprobada (2026-08-15) |
| 004 | React + TypeScript + Tailwind para Frontend | ✅ Aprobada (2026-08-15) |
| 005 | FastMCP para servidor de herramientas | ✅ Aprobada (2026-08-15) |
| 006 | WeasyPrint + Jinja2 para generación de PDFs | ✅ Aprobada (2026-08-15) |
| 007 | Arc42 + SOLID + TDD para calidad | ✅ Aprobada (2026-08-15) |

---

## Cómo Agregar un ADR

1. Crear archivo: `NNN-nombre-decision.md`
2. Seguir el template abajo
3. Revisar con Arquitecto
4. Actualizar tabla arriba
5. Hacer commit

## Template ADR

```markdown
# ADR NNN: Nombre de la Decisión

## Status
Propuesta / Aprobada / Deprecated / Superseded

## Context
[Contexto técnico, restricciones, problemas que motivan esta decisión]

## Decision
[Qué se decidió y por qué]

## Alternatives
[Opciones consideradas y por qué se rechazaron]

## Consequences
[Impacto positivo y negativo de esta decisión]

## Related Decisions
[Referencias a otras decisiones relacionadas]

## Date
YYYY-MM-DD

## Author
Arquitecto de Soluciones
```

---

**Última Actualización**: 2026-08-15  
**Total de ADRs**: 7 aprobadas  
**Arquitecto**: Carlos (cjhirashi@gmail.com)
