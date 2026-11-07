"""Distribuye los campos de texto anteriores de `projects` en los 3 campos markdown
nuevos (presentacion, tecnico, estado).

Uso (desde el host, con el contenedor de la API arriba):
    docker cp scripts/migrate_project_sections.py cjhirashi-career-api:/app/scripts/
    docker exec -w /app/src cjhirashi-career-api python /app/scripts/migrate_project_sections.py --dry-run
    docker exec -w /app/src cjhirashi-career-api python /app/scripts/migrate_project_sections.py

Reglas:
- Idempotente: solo rellena un campo nuevo si está vacío. No toca ni borra los campos anteriores.
- No pone `estado_verificado_el`: esa fecha la escribe quien comprueba el estado real.
- `--skip prj-44` omite proyectos que se redactan a mano.
"""
from __future__ import annotations

import argparse
import asyncio
import json

from sqlalchemy import text

from database import AsyncSessionLocal


def _block(heading: str, body: str | None) -> str:
    body = (body or "").strip()
    if not body:
        return ""
    return body if body.startswith("#") else f"## {heading}\n\n{body}"


def _repo_structure(raw: str | None) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    if raw.startswith("#"):
        return raw
    items = [i.strip() for i in raw.split(" · ") if i.strip()]
    body = "\n".join(f"- {i}" for i in items) if len(items) > 1 else raw
    return f"## Estructura del repositorio\n\n{body}"


def _results(raw) -> str:
    if not raw:
        return ""
    if isinstance(raw, dict):
        raw = [f"{k}: {v}" for k, v in raw.items()]
    items = [i if isinstance(i, str) else json.dumps(i, ensure_ascii=False) for i in raw]
    return "## Resultados\n\n" + "\n".join(f"- {i}" for i in items)


def build(row: dict) -> dict[str, str]:
    presentacion = "\n\n".join(
        b for b in (
            _block("Resumen", row["detailed_summary"]),
            _block("El problema", row["problem"]),
            _block("La solución", row["solution"]),
        ) if b
    )
    approach = (row["approach_steps"] or "").strip()
    approach_is_state = approach.lower().startswith("## estado")
    tecnico = "\n\n".join(
        b for b in (
            _block("Arquitectura", row["architecture"]),
            "" if approach_is_state else _block("Enfoque", approach),
            _repo_structure(row["repo_structure"]),
        ) if b
    )
    estado = "\n\n".join(
        b for b in (approach if approach_is_state else "", _results(row["results"])) if b
    )
    return {"presentacion": presentacion, "tecnico": tecnico, "estado": estado}


async def main(dry_run: bool, skip: set[str]) -> None:
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(text(
            "SELECT id, presentacion, tecnico, estado, detailed_summary, problem, solution, "
            "architecture, approach_steps, results, repo_structure FROM projects ORDER BY id"
        ))).mappings().all()
        for row in rows:
            if row["id"] in skip:
                print(f"{row['id']}: omitido")
                continue
            new = build(dict(row))
            updates = {k: v for k, v in new.items() if v and not row[k]}
            print(f"{row['id']}: {', '.join(f'{k}={len(v)}c' for k, v in updates.items()) or 'sin cambios'}")
            if updates and not dry_run:
                sets = ", ".join(f"{k} = :{k}" for k in updates)
                await session.execute(
                    text(f"UPDATE projects SET {sets} WHERE id = :id"), {**updates, "id": row["id"]}
                )
        if not dry_run:
            await session.commit()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip", nargs="*", default=[])
    args = ap.parse_args()
    asyncio.run(main(args.dry_run, set(args.skip)))
