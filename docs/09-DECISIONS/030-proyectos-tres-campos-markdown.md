# ADR-030: Documentación de proyectos en 3 campos markdown (`presentacion`, `tecnico`, `estado`)

## Estado

Aceptado — 2026-11-07 (decisión de Carlos; implementada sin spec previa por instrucción suya, con los cambios documentados aquí).

## Contexto

La página de detalle de un proyecto pintaba cinco bloques de texto con títulos fijos (`detailed_summary`, `problem`, `solution`, `architecture`, `approach_steps`) y no mostraba `results`, `notes`, `evidence_sources` ni `repo_structure`. El estado, las métricas y la hoja de ruta quedaban mezclados con la narrativa estable, así que cada avance obligaba a reescribir un texto largo y las fichas se quedaban atrás. Varios agentes (AIRA, Tukey, Banzi) documentan proyectos propios y necesitan una estructura genérica.

## Decisión

- La tabla `projects` gana tres columnas `Text` con markdown libre y una `Date`: `presentacion`, `tecnico`, `estado`, `estado_verificado_el`. Migración Alembic `5a1c7e9d2b30`, aditiva (no elimina ninguna columna).
- Los campos se agrupan por ritmo de cambio, y cada uno contiene secciones `##` propias:
  - `presentacion` (estable, es lo que vende): `## Resumen`, `## Qué ofrece`, `## Para quién`, `## El problema`, `## La solución`.
  - `tecnico` (cambia con la arquitectura): `## Arquitectura`, `## El producto en acción`, `## Enfoque`.
  - `estado` (cambia a menudo): `## Estado y operación`, `## Hoja de ruta` (en proyectos de datos, `## Resultados`).
- `estado_verificado_el` es la fecha en que alguien comprobó el estado real contra la fuente; la página la muestra como «Estado verificado el …». Solo la escribe quien verifica.
- El portafolio (`ProjectDetailPage`) muestra únicamente los tres campos nuevos más el stack; ya no pinta los campos anteriores. `GET /public/projects/{id}` devuelve los campos nuevos además de los anteriores.
- Los campos anteriores permanecen en la tabla y en la API de escritura como datos heredados, sin visualización. Su retiro será una migración aparte, cuando los 14 proyectos estén revisados.

## Migración de datos

`cjhirashi-career-api/scripts/migrate_project_sections.py` (idempotente, `--dry-run`, `--skip`) distribuye los campos anteriores en los nuevos sin sobrescribir lo ya escrito: resumen, problema y solución van a `presentacion`; arquitectura, enfoque y estructura del repositorio a `tecnico`; `results` (y el estado real de Hira) a `estado`. Aplicada el 2026-11-07 a 13 proyectos; Synapse (`prj-44`) se redactó a mano y se vaciaron sus campos anteriores. No escribe `estado_verificado_el`. Respaldo previo de la tabla en `../.respaldos-career/projects-antes-3-campos-2026-11-07.sql` (fuera del repo); imágenes anteriores etiquetadas `pre-3campos`.

## Consecuencias

- Quien escriba un proyecto (AIRA, Tukey, Banzi) rellena solo estos tres campos; escribir en los anteriores ya no tiene efecto visible.
- Los resultados de los proyectos de datos, que antes no se veían, aparecen bajo `## Resultados`.
- Pendiente: validar en escritura que cada campo traiga sus secciones; completar «Qué ofrece» y «Para quién» en los proyectos migrados mecánicamente; vaciar y retirar los campos anteriores.
