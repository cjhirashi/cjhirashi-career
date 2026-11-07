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
- El portafolio (`ProjectDetailPage`) muestra únicamente los tres campos nuevos más el stack; ya no pinta los campos anteriores. `GET /public/projects/{id}` devuelve los campos nuevos.
- Los campos anteriores (`detailed_summary`, `problem`, `solution`, `architecture`, `approach_steps`, `results`, `repo_structure`) se retiraron el mismo día con la migración `6b2d8f4a1c57`, una vez comprobado que ningún proyecto tenía contenido sin su equivalente nuevo. `notes`, `evidence_sources` y `releases` se conservan (no se pintan en la página).
- Convención de `## El producto en acción`: cada captura lleva debajo un pie de una o dos frases, en un párrafo en cursiva propio (`![alt](url)` + línea en blanco + `*pie*`). El portafolio lo estiliza con `.markdown-content p:has(> img:only-child) + p > em:only-child` (`index.css`).

## Migración de datos

El script `migrate_project_sections.py` (idempotente, `--dry-run`, `--skip`; retirado del repo tras el uso, disponible en el commit `d412c224`) distribuyó los campos anteriores en los nuevos sin sobrescribir lo ya escrito: resumen, problema y solución van a `presentacion`; arquitectura, enfoque y estructura del repositorio a `tecnico`; `results` (y el estado real de Hira) a `estado`. Aplicada el 2026-11-07 a 13 proyectos; Synapse (`prj-44`) se redactó a mano y se vaciaron sus campos anteriores. No escribe `estado_verificado_el`. Respaldos de la tabla fuera del repo, en `../.respaldos-career/`: `projects-antes-3-campos-2026-11-07.sql` (antes de la migración de datos) y `projects-antes-retiro-campos-viejos-2026-11-07.sql` (antes de eliminar las columnas). Imágenes anteriores etiquetadas `pre-3campos` y `pre-retiro-campos`. El `downgrade` de `6b2d8f4a1c57` recrea las columnas vacías; los datos se recuperan del respaldo.

## Consecuencias

- Quien escriba un proyecto (AIRA, Tukey, Banzi) rellena solo estos tres campos; escribir en los anteriores ya no tiene efecto visible.
- Los resultados de los proyectos de datos, que antes no se veían, aparecen bajo `## Resultados`.
- `scripts/import_vault.py` e `init.sql` ya estaban desfasados del modelo antes de este cambio (usan `tech_stack` e ids numéricos) y siguen sin actualizarse.
- Pendiente: validar en escritura que cada campo traiga sus secciones; completar «Qué ofrece» y «Para quién» en los proyectos migrados mecánicamente; pies de foto en las capturas de los proyectos de Tukey.
