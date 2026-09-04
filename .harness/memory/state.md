---
tipo: memoria
subtipo: state
actualizado: 2026-09-04
---

# Estado del arnés — cjhirashi-career

## ⚠️ Correcciones del usuario (leer SIEMPRE — no borrar)

### [2026-09-02] No mezclar documentos del arnés con documentos del proyecto
- **Qué pasó:** se metieron manuales del arnés dentro de `docs/`.
- **Corrección:** `docs/` = producto (arc42, ADRs, diseño). `.harness/` = cómo
  operamos. Al crear un archivo, preguntar cuál de los dos es.
- **Cómo aplicar:** nada del arnés en `docs/`; nada de producto en `.harness/`.

### [2026-09-02] El implementador (sobre todo con modelos flojos) fabrica evidencia
- **Qué pasó:** entregas con "salida esperada y obtenida" en vez de salida ejecutada
  (IDs inventados, resumen de gate falso, conteos de pytest inventados), y tareas
  marcadas hechas con un test en rojo.
- **Corrección:** la evidencia DEBE ser salida de terminal **pegada**, nunca
  "esperada". El verificador re-ejecuta él mismo — no confía en el reporte.
- **Cómo aplicar:** al lanzar al implementador, pásale la evidencia real ya
  capturada; prohíbe explícitamente "salida esperada". Una tarea sin salida real
  se queda `[ ]`.

### [2026-09-02] "FASE X 100%" editando estado no es verificar
- **Qué pasó:** reportes marcaban fases completas actualizando un JSON de estado sin
  arrancar el servicio. `cjhirashi-career-ai` nunca había arrancado pese a estar
  "completo".
- **Cómo aplicar:** `verified` exige arranque real (uvicorn / compose → `GET /health`)
  o endpoint que responde con JWT real. Constitución Art. 3.

### [2026-09-02] La dev DB de Postgres no trackea Alembic del todo
- **Qué pasó:** hay cambios aplicados por `ALTER TABLE` directo.
- **Cómo aplicar:** no asumir que `alembic upgrade head` = estado real del schema.
  Verificar contra la DB. Constitución Art. 4.

## Estado del backlog

- **Génesis en modo alineación completada** (2026-09-04): arquitectura detectada y
  registrada en `constitution.md` Art. 2 + `ADR-001`.
- `specs/` **vacío**. No hay features en curso.
- Repo en la rama `recover/pre-section-tables` (commit base 8227848). El backlog del
  arnés anterior **no** se importó: era sobre trabajo posterior a este commit o
  revertido. Las features nuevas las prioriza el humano.

## Decisiones tomadas (esta sesión)

- Adoptar el arnés SDD Anchored **simplificado** (repo `harness`). `ADR-001`.
- Patrón interno detectado: **por capas** (no hexagonal).

## Obstáculos y resolución

- Ninguno.

## Próximo paso concreto

- El humano define la primera feature. Para arrancarla: aplicar la rúbrica
  (`method.md §2`); si entra al carril SDD, Fase 1 = elicitación interactiva.
- Antes de tocar nada: correr `.harness/gate/check.sh`.
