"""Registro en código de la jerarquía de secciones del Admin (ADR-022).

Este módulo es la **fuente de estructura** (seed source): grupos → secciones L1
→ vistas. Lo consume ``services/admin_sections_seed.py::sync_structure`` para
poblar/mantener las 6 tablas reales (``admin_section_groups``,
``admin_sections_l1/l2/l3``, ``admin_views``). El catálogo efectivo en runtime lo
sirve ``services/section_catalog.py`` leyendo esas tablas (con caché).

Identificadores (ADR-022, supersede ADR-021):
- Una sección L1 es ``s1-<n>``. El entero ``<n>`` es el mismo que el ``sec-<n>``
  de ADR-021 (re-key 1:1); la migración ``c4d5e6f7a8b9`` lo congela.
- ``system_name`` es el slug legible (``dashboard``, ``career-projects``…),
  clave del upsert idempotente del seeder.
- L2/L3 no tienen estructura en código en este lote: el operador las creará con
  drag entre niveles (ADR-022 §Seguimiento).

REGLA DE NUMERACIÓN (CONGELADA): cada ``s1-<n>`` se asigna a mano, una vez y para
siempre. Sección nueva → siguiente entero libre. Sección retirada → hueco
permanente (no se reutiliza).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from services.bedrock.agent_profiles import (
    AGENT_CONFIGURATION,
    AGENT_DIGITAL_PRESENCE,
    AGENT_LINKEDIN_PUBLISHING,
    AGENT_METHODOLOGIES,
    AGENT_NETWORKING,
    AGENT_ORCHESTRATOR,
    AGENT_PDF_DESIGN,
    AGENT_PROFESSIONAL_IDENTITY,
    AGENT_SEARCH_OPERATIONS,
    AGENT_SETTINGS,
    AGENT_SUPPORT,
    AGENT_TASK_MANAGER,
    AGENT_VACANCY_SEARCH,
)

SECTION_TABLE = "table"
SECTION_FUNCTIONAL = "functional"
SECTION_METRICS = "metrics"
SECTION_BUCKET = "bucket"

SECTION_TYPES = (SECTION_TABLE, SECTION_FUNCTIONAL, SECTION_METRICS, SECTION_BUCKET)

SECTION_TYPE_LABELS = {
    SECTION_TABLE: "tabla",
    SECTION_FUNCTIONAL: "funcional",
    SECTION_METRICS: "métricas",
    SECTION_BUCKET: "bucket",
}

DATA_SOURCES = ("crud", "computed", "singleton", "external")

# Grupos del sidebar izquierdo. Valores CONGELADOS (ruling #2 de ADR-022).
# (grp_id, system_name, name, sort_order)
GROUPS: Tuple[Tuple[str, str, str, int], ...] = (
    ("grp-1", "metrics", "Métricas", 10),
    ("grp-2", "principal", "Principal", 15),
    ("grp-3", "storage", "Almacenamiento", 20),
    ("grp-4", "digital-presence", "Presencia Digital", 30),
    ("grp-5", "search-ops", "Operativa de Búsqueda", 31),
    ("grp-6", "pdf-design", "Diseño PDF", 40),
    ("grp-7", "agent-ai", "Agente IA", 51),
    ("grp-8", "settings", "Settings", 90),
    ("grp-9", "professional-identity", "Identidad Profesional", 100),
    ("grp-10", "networking", "Networking", 150),
    ("grp-11", "support", "Soporte", 160),
)

_GROUP_ID_BY_NAME: Dict[str, str] = {name: gid for gid, _sys, name, _so in GROUPS}


def _data_source_for(section_type: str, singleton: bool) -> str:
    if section_type == SECTION_METRICS:
        return "computed"
    if section_type in (SECTION_FUNCTIONAL, SECTION_BUCKET):
        return "external"
    return "singleton" if singleton else "crud"


@dataclass(frozen=True)
class AdminViewSpec:
    key: str
    label: str
    data_source: str
    resource_key: Optional[str] = None
    has_controls_window: bool = False
    tool_names: Tuple[str, ...] = ()


@dataclass(frozen=True)
class AdminSectionSpec:
    id: str  # PK de sección L1 ``s1-<n>`` (ADR-022, re-key 1:1 de ``sec-<n>``)
    system_name: str
    label: str
    path: str
    section_type: str
    group: str
    sort_order: int
    default_agent_profile_id: Optional[str] = None
    resource_key: Optional[str] = None
    related_tools: Tuple[str, ...] = ()
    singleton: bool = False
    views: Tuple[AdminViewSpec, ...] = field(default=())

    @property
    def group_id(self) -> str:
        return _GROUP_ID_BY_NAME[self.group]


def _auto_views(
    section_type: str,
    singleton: bool,
    resource_key: Optional[str],
    tool_names: Tuple[str, ...],
) -> Tuple[AdminViewSpec, ...]:
    ds = _data_source_for(section_type, singleton)
    rk = resource_key if ds in ("crud", "singleton") else None
    if section_type == SECTION_TABLE and not singleton:
        keys = (("list", "Lista"), ("view", "Vista"), ("edit", "Edición"))
    elif section_type == SECTION_TABLE and singleton:
        keys = (("main", "Ficha"),)
    else:
        keys = (("main", "Principal"),)
    return tuple(
        AdminViewSpec(key=k, label=lbl, data_source=ds, resource_key=rk, tool_names=tuple(tool_names))
        for k, lbl in keys
    )


def _section(
    number: int,
    system_name: str,
    label: str,
    path: str,
    section_type: str,
    group: str,
    sort_order: int,
    *,
    default_agent_profile_id: Optional[str] = None,
    resource_key: Optional[str] = None,
    related_tools: Tuple[str, ...] = (),
    singleton: bool = False,
    views: Optional[Tuple[AdminViewSpec, ...]] = None,
) -> AdminSectionSpec:
    resolved_views = views if views is not None else _auto_views(
        section_type, singleton, resource_key, related_tools
    )
    return AdminSectionSpec(
        id=f"s1-{number}",
        system_name=system_name,
        label=label,
        path=path,
        section_type=section_type,
        group=group,
        sort_order=sort_order,
        default_agent_profile_id=default_agent_profile_id,
        resource_key=resource_key,
        related_tools=tuple(related_tools),
        singleton=singleton,
        views=resolved_views,
    )


_LINKEDIN_TOOLS = (
    "get_linkedin_status",
    "list_linkedin_posts",
    "create_linkedin_post",
    "delete_scheduled_linkedin_post",
)
_JOB_DISCOVERY_TOOLS = (
    "list_job_providers",
    "run_job_discovery",
    "import_job_url",
    "save_job_listings",
)
_AUDIT_TOOLS = ("list_recent_changes", "restore_deleted_record")

_TASK_VIEWS: Tuple[AdminViewSpec, ...] = tuple(
    AdminViewSpec(key=k, label=lbl, data_source="crud", resource_key="agent-tasks")
    for k, lbl in (
        ("list", "Lista"),
        ("kanban", "Kanban"),
        ("calendar", "Calendario"),
        ("gantt", "Gantt"),
        ("view", "Vista"),
        ("edit", "Edición"),
    )
)


_STATIC_SECTIONS: List[AdminSectionSpec] = [
    _section(1, "dashboard", "Dashboard", "/dashboard", SECTION_METRICS, "Métricas", 10,
             default_agent_profile_id=AGENT_ORCHESTRATOR),
    _section(2, "metrics", "Métricas", "/metrics", SECTION_METRICS, "Métricas", 11,
             default_agent_profile_id=AGENT_ORCHESTRATOR),
    _section(3, "search-metrics", "Métricas de Búsqueda", "/search-metrics", SECTION_METRICS,
             "Métricas", 12, default_agent_profile_id=AGENT_SEARCH_OPERATIONS),
    _section(4, "agent-metrics", "Costo y Uso", "/agent/metrics", SECTION_METRICS, "Métricas", 13,
             default_agent_profile_id=AGENT_ORCHESTRATOR),
    _section(5, "files", "Archivos", "/files", SECTION_BUCKET, "Almacenamiento", 20,
             default_agent_profile_id=AGENT_ORCHESTRATOR),
    _section(6, "linkedin-publish", "LinkedIn · Publicar", "/linkedin", SECTION_FUNCTIONAL,
             "Presencia Digital", 30, default_agent_profile_id=AGENT_LINKEDIN_PUBLISHING,
             related_tools=_LINKEDIN_TOOLS),
    _section(7, "job-discovery", "Descubrir vacantes", "/job-discovery", SECTION_FUNCTIONAL,
             "Operativa de Búsqueda", 31, default_agent_profile_id=AGENT_VACANCY_SEARCH,
             related_tools=_JOB_DISCOVERY_TOOLS),
    _section(8, "pdf-templates", "Plantillas PDF", "/agent/pdf-templates", SECTION_TABLE,
             "Diseño PDF", 40, default_agent_profile_id=AGENT_PDF_DESIGN,
             resource_key="pdf-output-templates", related_tools=("pdf_template", "pdf_style")),
    _section(9, "pdf-styles", "Estilos PDF", "/agent/pdf-template-styles", SECTION_TABLE,
             "Diseño PDF", 41, default_agent_profile_id=AGENT_PDF_DESIGN,
             resource_key="pdf-template-styles", related_tools=("pdf_style", "pdf_template")),
    _section(10, "agent-tasks", "Tareas", "/tasks", SECTION_TABLE, "Principal", 15,
             default_agent_profile_id=AGENT_TASK_MANAGER, resource_key="agent-tasks",
             views=_TASK_VIEWS),
    _section(11, "agent-chat", "Chat General", "/agent/chat", SECTION_FUNCTIONAL, "Agente IA", 51,
             default_agent_profile_id=AGENT_ORCHESTRATOR),
    _section(12, "agent-memory", "Memoria", "/agent/memory", SECTION_FUNCTIONAL, "Agente IA", 52,
             default_agent_profile_id=AGENT_ORCHESTRATOR),
    _section(13, "agent-instructions", "Instrucciones", "/agent/instructions", SECTION_FUNCTIONAL,
             "Agente IA", 53, default_agent_profile_id=AGENT_ORCHESTRATOR),
    _section(14, "agent-tools", "Herramientas", "/agent/tools", SECTION_FUNCTIONAL, "Agente IA", 54,
             default_agent_profile_id=AGENT_ORCHESTRATOR),
    _section(15, "agent-audit-log", "Bitácora", "/agent/audit-log", SECTION_FUNCTIONAL, "Agente IA",
             55, default_agent_profile_id=AGENT_SETTINGS, related_tools=_AUDIT_TOOLS),
    _section(16, "settings-agents", "Catálogo de Agentes", "/settings/agents", SECTION_TABLE,
             "Settings", 90, default_agent_profile_id=AGENT_CONFIGURATION),
    _section(17, "settings-sections", "Secciones del Admin", "/settings/sections", SECTION_FUNCTIONAL,
             "Settings", 91, default_agent_profile_id=AGENT_CONFIGURATION),
    _section(18, "settings-agent-prompts", "Prompts Globales", "/settings/agent-prompts",
             SECTION_FUNCTIONAL, "Settings", 92, default_agent_profile_id=AGENT_CONFIGURATION),
    _section(19, "settings-error-reports", "Reportes de Falla", "/settings/error-reports",
             SECTION_TABLE, "Settings", 93, default_agent_profile_id=AGENT_SETTINGS,
             related_tools=("error_report_settings",)),
]

# (n, resource_key, label, agent_id, group, sort_order, singleton) — enteros CONGELADOS.
_CAREER_ROWS: List[Tuple[int, str, str, str, str, int, bool]] = [
    (20, "personal-profile", "Datos personales", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 100, True),
    (21, "differentiators", "Diferenciadores", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 101, False),
    (22, "identity", "Identidad", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 102, True),
    (23, "identity-reflections", "Reflexiones de identidad", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 103, False),
    (24, "competencies", "Competencias", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 104, False),
    (25, "certifications", "Certificaciones", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 105, False),
    (26, "target-roles", "Roles objetivo", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 106, False),
    (27, "work-history", "Historial laboral", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 107, False),
    (28, "achievements", "Logros", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 108, False),
    (29, "star-stories", "Historias STAR", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 109, False),
    (30, "career-reviews", "Revisiones de carrera", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 110, False),
    (31, "role-gap-analysis", "Análisis de brechas", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 111, False),
    (32, "projects", "Proyectos", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 112, False),
    (33, "fit-scoring-factors", "Factores de fit", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 120, False),
    (34, "market-segments", "Segmentos de mercado", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 121, False),
    (35, "role-narratives", "Narrativas de rol", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 122, False),
    (36, "search-plans", "Planes de búsqueda", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 123, False),
    (37, "networking-contacts", "Contactos", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 124, False),
    (38, "target-companies", "Empresas diana", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 125, False),
    (39, "vacancies", "Vacantes", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 126, False),
    (40, "cv-versions", "Versiones de CV", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 127, False),
    (41, "cover-letter-versions", "Cover letters", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 128, False),
    (42, "applications", "Aplicaciones", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 129, False),
    (43, "application-interactions", "Interacciones de aplicación", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 130, False),
    (44, "interviews", "Entrevistas", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 131, False),
    (45, "linkedin-profile", "Perfil de LinkedIn", AGENT_DIGITAL_PRESENCE, "Presencia Digital", 140, True),
    (46, "github-profile", "Perfil de GitHub", AGENT_DIGITAL_PRESENCE, "Presencia Digital", 141, True),
    (47, "portal-home", "Portal · Home", AGENT_DIGITAL_PRESENCE, "Presencia Digital", 142, True),
    (48, "portal-about", "Portal · Sobre Mí", AGENT_DIGITAL_PRESENCE, "Presencia Digital", 143, True),
    (49, "portal-contact", "Portal · Contacto", AGENT_DIGITAL_PRESENCE, "Presencia Digital", 144, True),
    (50, "publications", "Publicaciones", AGENT_DIGITAL_PRESENCE, "Presencia Digital", 145, False),
    (51, "contact-interactions", "Interacciones de contacto", AGENT_NETWORKING, "Networking", 150, False),
    (52, "networking-activities", "Actividades de networking", AGENT_NETWORKING, "Networking", 151, False),
    (53, "tags", "Tags", AGENT_SUPPORT, "Soporte", 160, False),
    (54, "operational-methodologies", "Metodologías Operativas", AGENT_METHODOLOGIES, "Soporte", 161, False),
]


def _career_section(row: Tuple[int, str, str, str, str, int, bool]) -> AdminSectionSpec:
    number, resource_key, label, agent_id, group, sort_order, singleton = row
    return _section(
        number,
        f"career-{resource_key}",
        label,
        f"/career/{resource_key}",
        SECTION_TABLE,
        group,
        sort_order,
        default_agent_profile_id=agent_id,
        resource_key=resource_key,
        singleton=singleton,
    )


_SECTIONS: List[AdminSectionSpec] = [*_STATIC_SECTIONS, *(_career_section(r) for r in _CAREER_ROWS)]

_BY_ID: Dict[str, AdminSectionSpec] = {s.id: s for s in _SECTIONS}
_BY_SYSTEM_NAME: Dict[str, AdminSectionSpec] = {s.system_name: s for s in _SECTIONS}
_BY_PATH: Dict[str, AdminSectionSpec] = {s.path: s for s in _SECTIONS}

# ---------------------------------------------------------------------------
# Aserciones de integridad del registro (abortan el import si el código está mal)
# ---------------------------------------------------------------------------

assert len(_BY_ID) == len(_SECTIONS), "PK s1-N duplicado en el registro de secciones"
assert len(_BY_SYSTEM_NAME) == len(_SECTIONS), "system_name duplicado en el registro"

_HIGH_WATER = 54
_SECTION_NUMBERS = [int(s.id.split("-")[1]) for s in _SECTIONS]
assert max(_SECTION_NUMBERS) <= _HIGH_WATER, "s1-N por encima de _HIGH_WATER: súbelo"
assert len(_SECTION_NUMBERS) == len(set(_SECTION_NUMBERS)), "entero s1-N colisionado"

_ALL_PATHS = [s.path for s in _SECTIONS if s.path]
assert len(_ALL_PATHS) == len(set(_ALL_PATHS)), "path duplicado entre secciones"

for _spec in _SECTIONS:
    assert _spec.group in _GROUP_ID_BY_NAME, f"grupo desconocido: {_spec.group!r} ({_spec.id})"
    assert _spec.section_type in SECTION_TYPES, f"section_type inválido en {_spec.id}"
    assert 0 < len(_spec.views) <= 10, f"{_spec.id}: una sección declara 0 o >10 vistas"
    _keys = [v.key for v in _spec.views]
    assert len(_keys) == len(set(_keys)), f"{_spec.id}: key de vista duplicada"
    for _v in _spec.views:
        assert _v.data_source in DATA_SOURCES, f"{_spec.id}/{_v.key}: data_source inválido"
        assert _v.resource_key is None or _v.data_source in ("crud", "singleton"), (
            f"{_spec.id}/{_v.key}: resource_key solo permitido en crud|singleton"
        )


# ---------------------------------------------------------------------------
# API pública del registro
# ---------------------------------------------------------------------------


def list_group_defs() -> Tuple[Tuple[str, str, str, int], ...]:
    """(grp_id, system_name, name, sort_order) de los 11 grupos, en orden de código."""
    return GROUPS


def list_section_specs() -> List[AdminSectionSpec]:
    return sorted(_SECTIONS, key=lambda s: (s.sort_order, s.label))


def get_section_spec(section_id: str) -> AdminSectionSpec:
    """Busca por PK L1 (``s1-N``)."""
    if section_id not in _BY_ID:
        raise KeyError(f"Unknown admin section: {section_id}")
    return _BY_ID[section_id]


def get_section_by_system_name(system_name: str) -> AdminSectionSpec:
    if system_name not in _BY_SYSTEM_NAME:
        raise KeyError(f"Unknown admin section (system_name): {system_name}")
    return _BY_SYSTEM_NAME[system_name]


def known_section_ids() -> set[str]:
    return set(_BY_ID.keys())


def match_section(route: str) -> Optional[Tuple[AdminSectionSpec, str]]:
    """(sección, view_key) para una ruta del Admin, o None.

    Conservado para compatibilidad y como base de ``section_catalog.match_active_view``.
    """
    if not route:
        return None
    path = route.split("?")[0].rstrip("/") or "/"
    if path in _BY_PATH:
        spec = _BY_PATH[path]
        return spec, spec.views[0].key
    prefixes = sorted(
        (s for s in _SECTIONS if path.startswith(f"{s.path}/")),
        key=lambda s: len(s.path),
        reverse=True,
    )
    if not prefixes:
        return None
    spec = prefixes[0]
    view_keys = {v.key for v in spec.views}
    if "view" in view_keys:
        return spec, "view"
    if "record" in view_keys:
        return spec, "record"
    return spec, spec.views[-1].key


def view_for(spec: AdminSectionSpec, view_key: str) -> AdminViewSpec:
    for view in spec.views:
        if view.key == view_key:
            return view
    return spec.views[0]
