"""
Vacantes: etapa del proceso y estado calculado (spec 007).

Funciones puras y sin BD. El catálogo de etapas es el único canon en código;
el modelo (CHECK), los schemas y el repositorio lo consumen desde aquí.
`vacancy_status` es derivado de `process_stage` y nunca se persiste ni se
acepta como entrada.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Literal, Optional, Tuple

ProcessStage = Literal[
    "not_applied",
    "applied",
    "screening",
    "hr_interview",
    "technical_interview",
    "technical_test",
    "final_interview",
    "offer",
    "hiring_process",
    "hired",
    "rejected",
    "withdrawn",
    "no_response",
]
VacancyStatus = Literal["pending", "in_process", "closed"]

# Orden canónico (el mismo del contrato de la spec).
PROCESS_STAGES: Tuple[str, ...] = (
    "not_applied",
    "applied",
    "screening",
    "hr_interview",
    "technical_interview",
    "technical_test",
    "final_interview",
    "offer",
    "hiring_process",
    "hired",
    "rejected",
    "withdrawn",
    "no_response",
)

STAGE_TO_STATUS: Dict[str, str] = {
    "not_applied": "pending",
    "applied": "in_process",
    "screening": "in_process",
    "hr_interview": "in_process",
    "technical_interview": "in_process",
    "technical_test": "in_process",
    "final_interview": "in_process",
    "offer": "in_process",
    "hiring_process": "in_process",
    "hired": "closed",
    "rejected": "closed",
    "withdrawn": "closed",
    "no_response": "closed",
}

DEFAULT_PROCESS_STAGE = "not_applied"

# Campos calculados / gestionados por el sistema: nunca se escriben desde fuera.
READ_ONLY_VACANCY_FIELDS = {"vacancy_status", "process_stage_updated_at"}


def vacancy_status_for(stage: str) -> str:
    """Estado de la vacante a partir de su etapa (nunca nulo)."""
    return STAGE_TO_STATUS[stage]


def stages_for_statuses(values: Iterable[str]) -> Tuple[str, ...]:
    """Etapas que corresponden a los estados dados; ignora estados desconocidos."""
    wanted = set(values)
    return tuple(s for s in PROCESS_STAGES if STAGE_TO_STATUS[s] in wanted)


def prepare_vacancy_write(
    data: Dict[str, Any],
    current_stage: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Normaliza el payload de escritura de una vacante.

    `current_stage=None` significa Create; con valor, Update sobre esa etapa.
    Quita los campos de sólo lectura, valida el catálogo (ValueError) y fija
    `process_stage_updated_at` sólo en Create o cuando la etapa cambia.
    """
    out = {k: v for k, v in data.items() if k not in READ_ONLY_VACANCY_FIELDS}
    is_create = current_stage is None

    if "process_stage" in out:
        stage = out["process_stage"]
        if stage is None:
            raise ValueError("process_stage no puede ser nulo")
        if stage not in PROCESS_STAGES:
            raise ValueError(
                f"process_stage inválido: {stage!r}. Valores permitidos: {', '.join(PROCESS_STAGES)}"
            )

    stage_changed = "process_stage" in out and out["process_stage"] != current_stage
    if is_create or stage_changed:
        out["process_stage_updated_at"] = now or datetime.now(timezone.utc)
    return out
