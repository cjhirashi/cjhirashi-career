"""
System prompt del harness: base, reglas globales (override en BD), sufijo por perfil y bloques por nivel.

Traslado de `cjhirashi-career-api/src/services/bedrock/prompt.py` y `bedrock_service.default_system_prompt`.
Cambios respecto a la API: los datos que vivían en la BD de carrera (metodologías asignadas, secciones) o
en Qdrant (notas de memoria) llegan por parámetro; `search_knowledge_base` se retira (D-15) y las
metodologías se leen por REST (`list_career_record` / `get_career_record`).
"""
import logging
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from repositories import profile_repo, settings_repo
from services.agent_profiles import (
    AGENT_METHODOLOGIES,
    AGENT_SEARCH_OPERATIONS,
    AGENT_VACANCY_SEARCH,
    AgentProfile,
    delegation_targets,
    get_profile,
    list_profiles,
    profile_can_read_methodologies,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Reglas de prompt del sistema
# ============================================================================

JOB_DISCOVERY_AUTH_RULE = (
    "Vacantes descubiertas: run_job_discovery solo hace preview (refs L1, L2…). "
    "Presenta empresa, rol, fuente y URL. No llames save_job_listings hasta que Carlos "
    "autorice refs concretas. save_job_listings(refs=...) crea vacancies pending_review "
    "para seguimiento en Vacantes. Nunca inventes vacantes ni uses create_career_record "
    "para ofertas de un discovery. Si Carlos pega una URL de vacante, importar y guardar "
    "esa ref sí está autorizado."
)

GROUNDING_RULE = (
    "REGLA CRÍTICA — NO ALUCINAR: Los datos de carrera viven en PostgreSQL, no en tu "
    "entrenamiento. Nunca inventes registros, IDs, títulos, fechas ni contenido. "
    "Antes de afirmar algo sobre un registro concreto (ej. ach-17, vac-5), consulta "
    "herramientas o el especialista dueño del dominio. Si la herramienta o el sub-turno "
    "devuelve not_found o vacío, dilo — no rellenes con suposiciones. Los IDs son "
    "prefijados (ach-17, cmp-42, trl-3)."
)

_L1_ORCHESTRATION_RULE = (
    "Nivel 1: no tienes CRUD ni tools de tarea. Cada pedido de datos o escritura "
    "se resuelve con delegate_to_specialist al L2 de esa área o al L3 de esa tarea. "
    "No respondas listados ni cifras de carrera sin haber delegado en este turno."
)

_L2_DOMAIN_RULE = (
    "Nivel 2: opera solo tu dominio. No llames a otro L2 ni al orquestador. "
    "Tareas transversales (bitácora, PDF de un registro, imágenes, plan de tareas, "
    "publicación LinkedIn, discovery de vacantes, redacción de CV o cover letter, "
    "consulta web, repos GitHub) se delegan a L3. "
    "Si piden listar TODO un recurso de tu dominio, usa list_career_record con limit=100 y pagina mientras "
    "has_more sea true. "
    "Si preguntan CUÁNTOS hay, llama count_career_records. "
    "Si necesitas revisar una o dos columnas puntuales (ej. nivel, category) en TODOS los "
    "registros de un resource_key, usa list_career_record con fields=['esa_columna'] — UNA "
    "llamada trae esa columna en cada item. Nunca hagas un get_career_record por cada registro "
    "para leer el mismo campo en todos: con 60-70 registros eso agota las rondas del turno antes "
    "de llegar a escribir nada."
    "Redactar en el chat no persiste: usa create_career_record o update_career_record "
    "(en diseño PDF: pdf_style / pdf_template). No afirmes que guardaste hasta que la tool "
    "devuelva el id. Si el usuario confirma (procede, adelante, hazlo), llama la tool en este turno. "
    "Si el cambio toca varios registros del mismo resource_key (ej. reclasificar todas las "
    "competencias en categorías nuevas), NO los anuncies uno por uno en texto: llama "
    "bulk_update_career_record con resource_key y updates=[{record_id, fields}, ...] en el mismo "
    "turno en que lo confirmas. 'Voy a actualizar cada uno' sin llamar la tool no cuenta como hecho. "
    "Esto también aplica a tareas de solo lectura o análisis sobre muchos registros: no termines "
    "el turno diciendo 'ahora voy a revisar/obtener X de cada uno' y te detengas ahí — ejecútalo "
    "en el mismo turno, ronda tras ronda, hasta terminar el lote completo o hasta que de verdad "
    "necesites que Carlos decida algo. Anunciar el próximo paso sin darlo no es progreso."
)

_L3_TASK_RULE = (
    "Nivel 3: no hablas con el usuario. Ejecuta la tarea con tus tools y devuelve "
    "un resumen factual (ids, URLs, errores). No delegues."
)

_METHODOLOGY_ASSIGNMENT_RULE = (
    "METODOLOGÍAS OPERATIVAS — solo las asignadas a ti. "
    "Cada metodología tiene `agent_profile_ids` (Admin Panel → Metodologías Operativas → Agentes). "
    "También puede tener `section_ids`, las Secciones del Admin a las que aplica. "
    "Las tuyas son las que incluyen tu perfil, más las compartidas (lista vacía = todos los agentes). "
    "No consultes ni apliques metodologías asignadas solo a otros agentes. "
    "Si Carlos crea una metodología nueva y te la asigna, es tuya de inmediato: consúltala y síguela. "
    "La asignación vive en el Admin, no en el código; no esperes que este prompt nombre cada metodología. "
    "Esta regla tiene prioridad sobre cualquier mención a una sección de metodología en el resto del prompt."
)

def _methodologies_grouped_by_section(
    assigned: List[Dict[str, Any]], section_labels: Optional[Dict[str, str]] = None
) -> List[str]:
    """Agrupa el catálogo de un L2 por sección de procedencia (spec 004, RF-008)."""
    labels = section_labels or {}
    by_section: Dict[str, List[Dict[str, Any]]] = {}
    shared: List[Dict[str, Any]] = []
    for row in assigned:
        sids = row.get("section_ids") or []
        if not sids:
            shared.append(row)
        else:
            for sid in sids:
                by_section.setdefault(sid, []).append(row)

    def _order(sid: str) -> int:
        tail = sid.split("-")[-1]
        return int(tail) if tail.isdigit() else 0

    out: List[str] = []
    for sid in sorted(by_section, key=_order):
        out.append(f"  Sección {sid} · {labels.get(sid, sid)}:")
        for row in by_section[sid]:
            out.append(f"    - {row['id']}: {row['title']}")
    if shared:
        out.append("  Compartidas (todas las secciones):")
        for row in shared:
            out.append(f"    - {row['id']}: {row['title']}")
    return out


def methodology_assignment_block(
    profile: AgentProfile,
    assigned: Optional[List[Dict[str, Any]]] = None,
    section_labels: Optional[Dict[str, str]] = None,
) -> str:
    """Regla + catálogo vigente (se recarga cada turno por REST)."""
    labels = section_labels or {}
    lines = [f"Tu perfil es `{profile.id}`."]
    if profile.id == AGENT_METHODOLOGIES:
        lines.append(
            "Eres el guardián: ves y mantienes TODAS las metodologías. "
            "Al crear o editar, llena agent_profile_ids con el agente dueño; "
            "vacío = compartida."
        )
    if assigned:
        lines.append("Metodologías vigentes que te corresponden (catálogo actualizado cada turno):")
        if profile.level == 2:
            lines.extend(_methodologies_grouped_by_section(assigned, labels))
        else:
            for row in assigned:
                names = [labels[s] for s in row.get("section_ids") or [] if s in labels]
                section = f" [{', '.join(names)}]" if names else ""
                shared = " (compartida)" if row.get("shared") else ""
                lines.append(f"- {row['id']}: {row['title']}{section}{shared}")
    else:
        lines.append(
            "En este momento no hay metodologías listadas para ti. "
            "Cuando Carlos te asigne una desde el Admin, aparecerá aquí y deberás consultarla."
        )
    if profile_can_read_methodologies(profile):
        lines.append(
            "Antes de operar una tabla o protocolo, identifica en el catálogo de arriba la metodología "
            "que aplica a ESTE trabajo y léela entera con get_career_record "
            "(resource_key=operational-methodologies, record_id=...). Si necesitas ver más, "
            "list_career_record sobre operational-methodologies sólo devuelve las asignadas a tu perfil "
            "o compartidas (el guardián ve todas). Lee sólo la que vas a aplicar ahora — una por trabajo, "
            "no todas las asignadas. Si el catálogo trae una metodología nueva, consúltala: es tuya."
        )
    else:
        lines.append(
            "No puedes leer metodologías directamente. Los especialistas que sí pueden "
            "consultan solo las metodologías asignadas a su propio perfil."
        )
    return "\n".join(lines)


def _agent_memory_block(notes: List[Dict[str, Any]]) -> str:
    if not notes:
        return (
            "MEMORIA PROPIA: Carlos puede dejar notas para este perfil en el "
            "catálogo de agentes. Ahora mismo no hay ninguna."
        )
    lines = ["MEMORIA PROPIA (notas de Carlos para este perfil; consúltalas siempre):"]
    for note in notes:
        text = (note.get("text") or "").strip()
        if text:
            lines.append(f"- {text}")
    return "\n".join(lines)


def _delegation_catalog_block(profile: AgentProfile, target_ids: Optional[List[str]] = None) -> str:
    if target_ids is None:
        targets = delegation_targets(profile)
    else:
        targets = []
        for tid in target_ids:
            try:
                targets.append(get_profile(tid))
            except KeyError:
                continue
    if not targets:
        return "Este perfil no tiene especialistas configurados para delegar."
    lines = [f"- {p.id} (L{p.level}) — {p.label}" for p in targets]
    return "Especialistas a los que puedes delegar:\n" + "\n".join(lines)


# ============================================================================
# Prompt base y reglas globales (override en BD)
# ============================================================================

def _known_resource_keys() -> List[str]:
    keys = {k for p in list_profiles() for k in (p.resource_keys or [])}
    return sorted(keys)


def default_system_prompt(resource_keys: Optional[Iterable[str]] = None) -> str:
    """Prompt base completo. Sin `resource_keys` se usan los de los perfiles."""
    resource_list = ", ".join(sorted(resource_keys if resource_keys is not None else _known_resource_keys()))
    return (
        "Eres el asistente de carrera dentro del Admin Panel de Carlos Jiménez Hirashi. "
        "Tienes acceso completo de lectura y escritura sobre sus datos de carrera a través de tus "
        "herramientas - puedes listar, obtener, crear, actualizar y eliminar registros directamente, "
        "sin pedir confirmación adicional del sistema (Carlos ya te la dio al usarte). "
        "Redactar el contenido en el chat no lo persiste: debes llamar las tools de escritura "
        "en el mismo turno; no afirmes que guardaste hasta que la tool devuelva el id. "
        "Antes de operar una tabla que no conozcas bien, consulta SOLO las metodologías operativas "
        "asignadas a tu perfil (campo Agentes / agent_profile_ids) más las compartidas (lista vacía), "
        "leyéndolas con list_career_record / get_career_record sobre operational-methodologies. "
        "Ahí está documentado cómo se relacionan las tablas y qué disciplina seguir. "
        "Una metodología nueva que Carlos te asigne desde el Admin es tuya de inmediato: consúltala; "
        "no esperes que el código la nombre. No apliques metodologías de otros agentes. "
        "Mantener el texto de las metodologías (crear/editar operational-methodologies) es del "
        "guardián agent_methodologies, salvo que Carlos te pida lo contrario. "
        "Antes de crear un registro en un recurso cuyos campos exactos no tengas ya confirmados (por un "
        "list_career_record o get_career_record previo en esta misma conversación), llama primero a "
        "describe_resource_schema - los nombres de columna reales no siempre son los que se adivinarían "
        "(ej. 'tags' usa tag_name/entity_type, no name/category). Evita adivinar campos a ciegas. "
        "Con registros grandes (p.ej. projects) llama get_career_record con 'fields' limitado a las "
        "columnas que vas a leer o editar; no traigas el registro completo para tocar 1-2 campos. "
        "Para una petición de varios pasos (ej. 'actualiza toda mi sección de Identidad' o cualquier tarea "
        "que tome más de 2-3 llamadas a herramientas), usa el resource_key 'agent-tasks' (fields: title, "
        "description, status) para planear primero: crea una tarea por paso con status='pending', y ve "
        "actualizando cada una a 'in_progress' antes de ejecutarla y a 'done' al terminarla (o "
        "'cancelled' si ya no aplica) - así Carlos puede ver el plan avanzar, y tú puedes retomarlo en "
        "otra conversación si esta se corta a la mitad. Para un mensaje simple de un solo paso, no hace "
        "falta crear una tarea. "
        "Cada create/update/delete que haces queda registrado automáticamente en la bitácora, con el "
        "estado completo del registro antes y después - no necesitas escribir nada ahí tú mismo. Usa "
        "list_recent_changes si Carlos pregunta qué hiciste, o si necesitas confirmar un cambio antes de "
        "seguir. Si Carlos te pide deshacer algo que eliminaste (en esta conversación o una anterior), "
        "usa list_recent_changes para encontrar el audit_id de esa eliminación y luego "
        "restore_deleted_record - no lo recrees a mano con create_career_record, el registro restaurado "
        "debe salir exactamente del estado que guardó la bitácora. "
        "Responde siempre en español, de forma clara y directa sobre qué hiciste. "
        "No envuelvas la respuesta al usuario en etiquetas de razonamiento interno "
        "(<thinking>, </thinking>, <think>, </think>). "
        f"Recursos disponibles (resource_key): {resource_list}."
    )


def default_global_rules() -> str:
    """Reglas globales (todo agente) — reemplazo total, no aditivo, igual que el prompt base."""
    return "\n\n".join([GROUNDING_RULE, _METHODOLOGY_ASSIGNMENT_RULE])


# ============================================================================
# Composición del system prompt
# ============================================================================

async def compose_system_prompt(
    db: AsyncSession,
    profile: AgentProfile,
    page_context: Optional[dict],
    *,
    assigned: Optional[List[Dict[str, Any]]] = None,
    notes: Optional[List[Dict[str, Any]]] = None,
    delegate_ids: Optional[List[str]] = None,
    section_labels: Optional[Dict[str, str]] = None,
) -> str:
    """Compone el prompt del turno. `assigned` (metodologías) y `notes` (memoria) los carga quien llama."""
    base = await settings_repo.get_system_prompt_override(db) or default_system_prompt()
    global_rules = await settings_repo.get_global_rules_override(db) or default_global_rules()
    suffix = await profile_repo.get_prompt_suffix(db, profile.id) or profile.system_prompt_suffix
    parts = [
        base,
        "Las reglas de nivel de este perfil tienen prioridad sobre el prompt global si hay conflicto.",
        global_rules,
        methodology_assignment_block(profile, assigned or [], section_labels),
        suffix,
    ]
    if notes is not None and profile.user_facing:
        parts.append(_agent_memory_block(notes))
    if page_context and page_context.get("resource_key"):
        title = page_context.get("page_title") or page_context["resource_key"]
        parts.append(
            f"El usuario está en {title} (resource_key={page_context['resource_key']}). "
            "Prioriza operaciones sobre ese recurso salvo que pida otra cosa."
        )
    route = (page_context or {}).get("route") or ""
    if profile.level == 1:
        parts.append(_L1_ORCHESTRATION_RULE)
        parts.append(_delegation_catalog_block(profile, delegate_ids))
    elif profile.level == 2:
        parts.append(_L2_DOMAIN_RULE)
        parts.append(_delegation_catalog_block(profile, delegate_ids))
    else:
        parts.append(_L3_TASK_RULE)
    if profile.id in (AGENT_SEARCH_OPERATIONS, AGENT_VACANCY_SEARCH) or route == "/job-discovery":
        parts.append(JOB_DISCOVERY_AUTH_RULE)
    return "\n\n".join(p for p in parts if p)
