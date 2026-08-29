"""ADR-022: jerarquía de secciones del Admin + vistas en tablas reales.

Crea 5 tablas (``admin_section_groups``, ``admin_sections_l1/l2/l3``,
``admin_views``), las siembra con un snapshot **CONGELADO embebido** (esta
migración NO importa ``services.admin_sections`` para no acoplar el historial al
código de la app), convierte las filas de ``admin_section_overrides`` (ADR-021) y
hace ``DROP`` de esa tabla.

Re-key 1:1: ``sec-N`` → ``s1-N`` (mismo entero). L2/L3 quedan vacías (el operador
las poblará con drag entre niveles — ADR-022 §Seguimiento).

Nota de deploy (igual que b1c2d3e4f5a6 / ADR-019 y b2c3d4e5f6a7 / ADR-021): esto
**NO corre en ``init_db``** (que usa ``create_all`` + el seeder idempotente
``services/admin_sections_seed.py``). Tras el rebuild hay que ejecutar
``alembic upgrade head`` en el mismo paso.

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-08-28
"""
import logging
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, tuple, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_log = logging.getLogger("alembic.runtime.migration")

_JSON = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

# ---------------------------------------------------------------------------
# Mapas CONGELADOS embebidos (ver tests/unit/test_admin_sections_migration_map.py)
# ---------------------------------------------------------------------------

# (grp_id, system_name, name, sort_order)
_FROZEN_GROUPS = [
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
]
_GROUP_ID_BY_NAME = {name: gid for gid, _s, name, _o in _FROZEN_GROUPS}

_LINKEDIN_TOOLS = (
    "get_linkedin_status",
    "list_linkedin_posts",
    "create_linkedin_post",
    "delete_scheduled_linkedin_post",
)
_JOB_DISCOVERY_TOOLS = ("list_job_providers", "run_job_discovery", "import_job_url", "save_job_listings")
_AUDIT_TOOLS = ("list_recent_changes", "restore_deleted_record")

# (n, system_name, label, path, section_type, group_name, sort_order, singleton, default_agent, tools)
_SECTIONS = [
    (1, "dashboard", "Dashboard", "/dashboard", "metrics", "Métricas", 10, False, "agent_orchestrator", ()),
    (2, "metrics", "Métricas", "/metrics", "metrics", "Métricas", 11, False, "agent_orchestrator", ()),
    (3, "search-metrics", "Métricas de Búsqueda", "/search-metrics", "metrics", "Métricas", 12, False, "agent_search_operations", ()),
    (4, "agent-metrics", "Costo y Uso", "/agent/metrics", "metrics", "Métricas", 13, False, "agent_orchestrator", ()),
    (5, "files", "Archivos", "/files", "bucket", "Almacenamiento", 20, False, "agent_orchestrator", ()),
    (6, "linkedin-publish", "LinkedIn · Publicar", "/linkedin", "functional", "Presencia Digital", 30, False, "agent_linkedin_publishing", _LINKEDIN_TOOLS),
    (7, "job-discovery", "Descubrir vacantes", "/job-discovery", "functional", "Operativa de Búsqueda", 31, False, "agent_vacancy_search", _JOB_DISCOVERY_TOOLS),
    (8, "pdf-templates", "Plantillas PDF", "/agent/pdf-templates", "table", "Diseño PDF", 40, False, "agent_pdf_design", ("pdf_template", "pdf_style")),
    (9, "pdf-styles", "Estilos PDF", "/agent/pdf-template-styles", "table", "Diseño PDF", 41, False, "agent_pdf_design", ("pdf_style", "pdf_template")),
    (10, "agent-tasks", "Tareas", "/tasks", "table", "Principal", 15, False, "agent_task_manager", ()),
    (11, "agent-chat", "Chat General", "/agent/chat", "functional", "Agente IA", 51, False, "agent_orchestrator", ()),
    (12, "agent-memory", "Memoria", "/agent/memory", "functional", "Agente IA", 52, False, "agent_orchestrator", ()),
    (13, "agent-instructions", "Instrucciones", "/agent/instructions", "functional", "Agente IA", 53, False, "agent_orchestrator", ()),
    (14, "agent-tools", "Herramientas", "/agent/tools", "functional", "Agente IA", 54, False, "agent_orchestrator", ()),
    (15, "agent-audit-log", "Bitácora", "/agent/audit-log", "functional", "Agente IA", 55, False, "agent_settings", _AUDIT_TOOLS),
    (16, "settings-agents", "Catálogo de Agentes", "/settings/agents", "table", "Settings", 90, False, "agent_configuration", ()),
    (17, "admin-sections", "Secciones del Admin", "/settings/sections", "functional", "Settings", 91, False, "agent_configuration", ()),
    (18, "settings-agent-prompts", "Prompts Globales", "/settings/agent-prompts", "functional", "Settings", 92, False, "agent_configuration", ()),
    (19, "settings-error-reports", "Reportes de Falla", "/settings/error-reports", "table", "Settings", 93, False, "agent_settings", ("error_report_settings",)),
    (20, "career-personal-profile", "Datos personales", "/career/personal-profile", "table", "Identidad Profesional", 100, True, "agent_professional_identity", ()),
    (21, "career-differentiators", "Diferenciadores", "/career/differentiators", "table", "Identidad Profesional", 101, False, "agent_professional_identity", ()),
    (22, "career-identity", "Identidad", "/career/identity", "table", "Identidad Profesional", 102, True, "agent_professional_identity", ()),
    (23, "career-identity-reflections", "Reflexiones de identidad", "/career/identity-reflections", "table", "Identidad Profesional", 103, False, "agent_professional_identity", ()),
    (24, "career-competencies", "Competencias", "/career/competencies", "table", "Identidad Profesional", 104, False, "agent_professional_identity", ()),
    (25, "career-certifications", "Certificaciones", "/career/certifications", "table", "Identidad Profesional", 105, False, "agent_professional_identity", ()),
    (26, "career-target-roles", "Roles objetivo", "/career/target-roles", "table", "Identidad Profesional", 106, False, "agent_professional_identity", ()),
    (27, "career-work-history", "Historial laboral", "/career/work-history", "table", "Identidad Profesional", 107, False, "agent_professional_identity", ()),
    (28, "career-achievements", "Logros", "/career/achievements", "table", "Identidad Profesional", 108, False, "agent_professional_identity", ()),
    (29, "career-star-stories", "Historias STAR", "/career/star-stories", "table", "Identidad Profesional", 109, False, "agent_professional_identity", ()),
    (30, "career-career-reviews", "Revisiones de carrera", "/career/career-reviews", "table", "Identidad Profesional", 110, False, "agent_professional_identity", ()),
    (31, "career-role-gap-analysis", "Análisis de brechas", "/career/role-gap-analysis", "table", "Identidad Profesional", 111, False, "agent_professional_identity", ()),
    (32, "career-projects", "Proyectos", "/career/projects", "table", "Identidad Profesional", 112, False, "agent_professional_identity", ()),
    (33, "career-fit-scoring-factors", "Factores de fit", "/career/fit-scoring-factors", "table", "Operativa de Búsqueda", 120, False, "agent_search_operations", ()),
    (34, "career-market-segments", "Segmentos de mercado", "/career/market-segments", "table", "Operativa de Búsqueda", 121, False, "agent_search_operations", ()),
    (35, "career-role-narratives", "Narrativas de rol", "/career/role-narratives", "table", "Operativa de Búsqueda", 122, False, "agent_search_operations", ()),
    (36, "career-search-plans", "Planes de búsqueda", "/career/search-plans", "table", "Operativa de Búsqueda", 123, False, "agent_search_operations", ()),
    (37, "career-networking-contacts", "Contactos", "/career/networking-contacts", "table", "Operativa de Búsqueda", 124, False, "agent_search_operations", ()),
    (38, "career-target-companies", "Empresas diana", "/career/target-companies", "table", "Operativa de Búsqueda", 125, False, "agent_search_operations", ()),
    (39, "career-vacancies", "Vacantes", "/career/vacancies", "table", "Operativa de Búsqueda", 126, False, "agent_search_operations", ()),
    (40, "career-cv-versions", "Versiones de CV", "/career/cv-versions", "table", "Operativa de Búsqueda", 127, False, "agent_search_operations", ()),
    (41, "career-cover-letter-versions", "Cover letters", "/career/cover-letter-versions", "table", "Operativa de Búsqueda", 128, False, "agent_search_operations", ()),
    (42, "career-applications", "Aplicaciones", "/career/applications", "table", "Operativa de Búsqueda", 129, False, "agent_search_operations", ()),
    (43, "career-application-interactions", "Interacciones de aplicación", "/career/application-interactions", "table", "Operativa de Búsqueda", 130, False, "agent_search_operations", ()),
    (44, "career-interviews", "Entrevistas", "/career/interviews", "table", "Operativa de Búsqueda", 131, False, "agent_search_operations", ()),
    (45, "career-linkedin-profile", "Perfil de LinkedIn", "/career/linkedin-profile", "table", "Presencia Digital", 140, True, "agent_digital_presence", ()),
    (46, "career-github-profile", "Perfil de GitHub", "/career/github-profile", "table", "Presencia Digital", 141, True, "agent_digital_presence", ()),
    (47, "career-portal-home", "Portal · Home", "/career/portal-home", "table", "Presencia Digital", 142, True, "agent_digital_presence", ()),
    (48, "career-portal-about", "Portal · Sobre Mí", "/career/portal-about", "table", "Presencia Digital", 143, True, "agent_digital_presence", ()),
    (49, "career-portal-contact", "Portal · Contacto", "/career/portal-contact", "table", "Presencia Digital", 144, True, "agent_digital_presence", ()),
    (50, "career-publications", "Publicaciones", "/career/publications", "table", "Presencia Digital", 145, False, "agent_digital_presence", ()),
    (51, "career-contact-interactions", "Interacciones de contacto", "/career/contact-interactions", "table", "Networking", 150, False, "agent_networking", ()),
    (52, "career-networking-activities", "Actividades de networking", "/career/networking-activities", "table", "Networking", 151, False, "agent_networking", ()),
    (53, "career-tags", "Tags", "/career/tags", "table", "Soporte", 160, False, "agent_support", ()),
    (54, "career-operational-methodologies", "Metodologías Operativas", "/career/operational-methodologies", "table", "Soporte", 161, False, "agent_methodologies", ()),
]

_SEC_TO_S1 = {f"sec-{n}": f"s1-{n}" for n in range(1, 55)}

_PROFILE_LEVELS = {
    "agent_orchestrator": 1,
    "agent_professional_identity": 2,
    "agent_search_operations": 2,
    "agent_digital_presence": 2,
    "agent_networking": 2,
    "agent_support": 2,
    "agent_methodologies": 2,
    "agent_pdf_design": 2,
    "agent_settings": 2,
    "agent_configuration": 2,
    "agent_task_manager": 3,
    "agent_linkedin_publishing": 3,
    "agent_vacancy_search": 3,
    "agent_github": 3,
    "agent_changelog": 3,
}

_L3_CHAT_FALLBACK = {
    "agent_linkedin_publishing": "agent_digital_presence",
    "agent_vacancy_search": "agent_search_operations",
    "agent_github": "agent_digital_presence",
    "agent_task_manager": "agent_orchestrator",  # L1 ⇒ NULL
}

_TASK_VIEW_KEYS = [
    ("list", "Lista"),
    ("kanban", "Kanban"),
    ("calendar", "Calendario"),
    ("gantt", "Gantt"),
    ("view", "Vista"),
    ("edit", "Edición"),
]


def _data_source(section_type: str, singleton: bool) -> str:
    if section_type == "metrics":
        return "computed"
    if section_type in ("functional", "bucket"):
        return "external"
    return "singleton" if singleton else "crud"


def _views_for(n, system_name, section_type, singleton, tools):
    resource_key = system_name[len("career-"):] if system_name.startswith("career-") else {
        "pdf-templates": "pdf-output-templates",
        "pdf-styles": "pdf-template-styles",
        "agent-tasks": "agent-tasks",
    }.get(system_name)
    if n == 10:
        keys = _TASK_VIEW_KEYS
        ds, rk = "crud", "agent-tasks"
    else:
        ds = _data_source(section_type, singleton)
        rk = resource_key if ds in ("crud", "singleton") else None
        if section_type == "table" and not singleton:
            keys = [("list", "Lista"), ("view", "Vista"), ("edit", "Edición")]
        elif section_type == "table" and singleton:
            keys = [("main", "Ficha")]
        else:
            keys = [("main", "Principal")]
    return [
        {"key": k, "label": lbl, "sort_order": i, "data_source": ds, "resource_key": rk,
         "tool_names": list(tools)}
        for i, (k, lbl) in enumerate(keys)
    ]


def _responsible(default_agent):
    if not default_agent:
        return None
    lvl = _PROFILE_LEVELS.get(default_agent)
    if lvl == 2:
        return default_agent
    if lvl == 1:
        return None
    fb = _L3_CHAT_FALLBACK.get(default_agent)
    return fb if fb and _PROFILE_LEVELS.get(fb) == 2 else None


def _plan():
    """Devuelve (groups, l1_rows, views) totalmente materializados con ids congelados."""
    groups = [
        {"id": gid, "system_name": s, "name": name, "sort_order": so}
        for gid, s, name, so in _FROZEN_GROUPS
    ]
    l1_rows = []
    views = []
    principal_by_s1 = {}
    counter = 0
    for (n, system_name, label, path, stype, group_name, so, singleton, agent, tools) in sorted(
        _SECTIONS, key=lambda r: r[0]
    ):
        s1_id = _SEC_TO_S1[f"sec-{n}"]
        l1_rows.append(
            {
                "id": s1_id,
                "group_id": _GROUP_ID_BY_NAME[group_name],
                "system_name": system_name,
                "label": label,
                "path": path,
                "section_type": stype,
                "sort_order": so,
            }
        )
        for vi, v in enumerate(_views_for(n, system_name, stype, singleton, tools)):
            counter += 1
            vw_id = f"vw-{counter}"
            responsible = _responsible(agent) if vi == 0 else None
            views.append(
                {
                    "id": vw_id,
                    "owner_l1_id": s1_id,
                    "key": v["key"],
                    "label": v["label"],
                    "sort_order": v["sort_order"],
                    "has_controls_window": False,
                    "tool_names": v["tool_names"],
                    "data_source": v["data_source"],
                    "resource_key": v["resource_key"],
                    "responsible_agent_profile_id": responsible,
                }
            )
            if vi == 0:
                principal_by_s1[s1_id] = vw_id
    return groups, l1_rows, views, principal_by_s1


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------


def _create_tables(inspector) -> None:
    if not inspector.has_table("admin_section_groups"):
        op.create_table(
            "admin_section_groups",
            sa.Column("id", sa.String(20), primary_key=True),
            sa.Column("system_name", sa.String(60), nullable=False, unique=True),
            sa.Column("name", sa.String(120), nullable=False, unique=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_admin_section_groups_sort", "admin_section_groups", ["sort_order"])

    for level, parent in ((1, None), (2, 1), (3, 2)):
        table = f"admin_sections_l{level}"
        if inspector.has_table(table):
            continue
        cols = [
            sa.Column("id", sa.String(20), primary_key=True),
            sa.Column("system_name", sa.String(80), nullable=False, unique=True),
            sa.Column("label", sa.String(120), nullable=False),
            sa.Column("path", sa.String(120), nullable=True),
            sa.Column("section_type", sa.String(20), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("origin", sa.String(16), nullable=False, server_default="code"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint(
                "section_type IN ('table', 'functional', 'metrics', 'bucket')",
                name=f"ck_{table}_section_type",
            ),
        ]
        if level == 1:
            cols.insert(
                1,
                sa.Column(
                    "group_id",
                    sa.String(20),
                    sa.ForeignKey("admin_section_groups.id", ondelete="RESTRICT"),
                    nullable=False,
                ),
            )
        else:
            cols.insert(
                1,
                sa.Column(
                    f"parent_l{parent}_id",
                    sa.String(20),
                    sa.ForeignKey(f"admin_sections_l{parent}.id", ondelete="CASCADE"),
                    nullable=False,
                ),
            )
        op.create_table(table, *cols)
        op.create_index(
            f"uq_{table}_path", table, ["path"], unique=True,
            postgresql_where=sa.text("path IS NOT NULL"),
        )
        parent_col = "group_id" if level == 1 else f"parent_l{parent}_id"
        op.create_index(f"ix_{table}_parent_sort", table, [parent_col, "sort_order"])

    if not inspector.has_table("admin_views"):
        op.create_table(
            "admin_views",
            sa.Column("id", sa.String(20), primary_key=True),
            sa.Column("owner_l1_id", sa.String(20), sa.ForeignKey("admin_sections_l1.id", ondelete="CASCADE"), nullable=True),
            sa.Column("owner_l2_id", sa.String(20), sa.ForeignKey("admin_sections_l2.id", ondelete="CASCADE"), nullable=True),
            sa.Column("owner_l3_id", sa.String(20), sa.ForeignKey("admin_sections_l3.id", ondelete="CASCADE"), nullable=True),
            sa.Column("key", sa.String(40), nullable=False),
            sa.Column("label", sa.String(120), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("has_controls_window", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("tool_names", _JSON, nullable=False, server_default=sa.text("'[]'")),
            sa.Column("data_source", sa.String(20), nullable=False, server_default="crud"),
            sa.Column("resource_key", sa.String(80), nullable=True),
            sa.Column("responsible_agent_profile_id", sa.String(50), nullable=True),
            sa.Column("instructions", sa.Text(), nullable=True),
            sa.Column("origin", sa.String(16), nullable=False, server_default="code"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint(
                "(CASE WHEN owner_l1_id IS NOT NULL THEN 1 ELSE 0 END"
                " + CASE WHEN owner_l2_id IS NOT NULL THEN 1 ELSE 0 END"
                " + CASE WHEN owner_l3_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
                name="ck_admin_views_single_owner",
            ),
            sa.CheckConstraint(
                "data_source IN ('crud', 'computed', 'singleton', 'external')",
                name="ck_admin_views_data_source",
            ),
            sa.CheckConstraint(
                "resource_key IS NULL OR data_source IN ('crud', 'singleton')",
                name="ck_admin_views_resource_key_scope",
            ),
        )
        for lvl in (1, 2, 3):
            col = f"owner_l{lvl}_id"
            op.create_index(
                f"uq_admin_views_l{lvl}_key", "admin_views", [col, "key"], unique=True,
                postgresql_where=sa.text(f"{col} IS NOT NULL"),
            )
            op.create_index(f"ix_admin_views_l{lvl}_sort", "admin_views", [col, "sort_order"])
        op.create_index(
            "ix_admin_views_responsible", "admin_views", ["responsible_agent_profile_id"]
        )


def _seed(bind, groups, l1_rows, views) -> None:
    for g in groups:
        bind.execute(
            sa.text(
                "INSERT INTO admin_section_groups (id, system_name, name, sort_order) "
                "VALUES (:id, :system_name, :name, :sort_order) ON CONFLICT (id) DO NOTHING"
            ),
            g,
        )
    for row in l1_rows:
        bind.execute(
            sa.text(
                "INSERT INTO admin_sections_l1 "
                "(id, group_id, system_name, label, path, section_type, sort_order, origin) "
                "VALUES (:id, :group_id, :system_name, :label, :path, :section_type, :sort_order, 'code') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            row,
        )
    for v in views:
        bind.execute(
            sa.text(
                "INSERT INTO admin_views "
                "(id, owner_l1_id, key, label, sort_order, has_controls_window, tool_names, "
                " data_source, resource_key, responsible_agent_profile_id, origin) "
                "VALUES (:id, :owner_l1_id, :key, :label, :sort_order, :has_controls_window, "
                " CAST(:tool_names AS JSONB), :data_source, :resource_key, "
                " :responsible_agent_profile_id, 'code') "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {
                "id": v["id"],
                "owner_l1_id": v["owner_l1_id"],
                "key": v["key"],
                "label": v["label"],
                "sort_order": v["sort_order"],
                "has_controls_window": v["has_controls_window"],
                "tool_names": _json_dumps(v["tool_names"]),
                "data_source": v["data_source"],
                "resource_key": v["resource_key"],
                "responsible_agent_profile_id": v["responsible_agent_profile_id"],
            },
        )


def _json_dumps(value) -> str:
    import json

    return json.dumps(value)


def _convert_overrides(bind, inspector, principal_by_s1) -> None:
    if not inspector.has_table("admin_section_overrides"):
        return
    rows = bind.execute(
        sa.text(
            "SELECT section_id, agent_profile_id, description, views FROM admin_section_overrides"
        )
    ).fetchall()

    # instrucciones acumuladas por vw_id
    extra_instructions: dict = {}
    responsible_updates: dict = {}

    for section_id, agent_profile_id, description, views_json in rows:
        s1_id = _SEC_TO_S1.get(section_id)
        if s1_id is None:
            _log.warning("ADR-022 conversión: override %r sin mapa sec-N; se ignora", section_id)
            continue
        principal_vw = principal_by_s1.get(s1_id)

        if description and str(description).strip():
            extra_instructions.setdefault(principal_vw, []).insert(0, str(description).strip())

        view_map = views_json if isinstance(views_json, dict) else {}
        if isinstance(views_json, str):
            try:
                view_map = _json_loads(views_json)
            except Exception:
                view_map = {}
        for view_key, payload in (view_map or {}).items():
            if not isinstance(payload, dict):
                continue
            target = bind.execute(
                sa.text(
                    "SELECT id FROM admin_views WHERE owner_l1_id = :oid AND key = :k"
                ),
                {"oid": s1_id, "k": view_key},
            ).scalar()
            if target is None:
                _log.warning(
                    "ADR-022 conversión: %s view_key %r inexistente; se ignora", s1_id, view_key
                )
                continue
            piece = "\n\n".join(
                p for p in (
                    payload.get("sidebar_title"),
                    payload.get("sidebar_body"),
                    payload.get("description"),
                )
                if p and str(p).strip()
            )
            if piece:
                extra_instructions.setdefault(target, []).append(piece)

        if agent_profile_id:
            if _PROFILE_LEVELS.get(agent_profile_id) == 2:
                responsible_updates[principal_vw] = agent_profile_id
            else:
                _log.warning(
                    "ADR-022 conversión: override %s agent %r no es L2; se descarta",
                    section_id,
                    agent_profile_id,
                )

    for vw_id, pieces in extra_instructions.items():
        if not vw_id or not pieces:
            continue
        bind.execute(
            sa.text(
                "UPDATE admin_views SET instructions = :txt WHERE id = :id AND "
                "(instructions IS NULL OR instructions = '')"
            ),
            {"txt": "\n\n".join(pieces), "id": vw_id},
        )
    for vw_id, agent in responsible_updates.items():
        if not vw_id:
            continue
        bind.execute(
            sa.text("UPDATE admin_views SET responsible_agent_profile_id = :a WHERE id = :id"),
            {"a": agent, "id": vw_id},
        )


def _json_loads(value: str):
    import json

    return json.loads(value)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    _create_tables(inspector)
    for prefix in ("grp", "s1", "s2", "s3", "vw"):
        op.execute(sa.text(f"CREATE SEQUENCE IF NOT EXISTS {prefix}_id_seq START 1"))

    groups, l1_rows, views, principal_by_s1 = _plan()
    _seed(bind, groups, l1_rows, views)
    _convert_overrides(bind, inspector, principal_by_s1)

    if inspector.has_table("admin_section_overrides"):
        op.drop_table("admin_section_overrides")


# ---------------------------------------------------------------------------
# downgrade (best-effort, sin round-trip perfecto)
# ---------------------------------------------------------------------------


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("admin_section_overrides"):
        op.create_table(
            "admin_section_overrides",
            sa.Column("section_id", sa.String(40), primary_key=True),
            sa.Column("agent_profile_id", sa.String(50), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("views", _JSON, nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if inspector.has_table("admin_views"):
        _groups, _l1, views, principal_by_s1 = _plan()
        seed_default = {v["owner_l1_id"]: v["responsible_agent_profile_id"] for v in views if v["sort_order"] == 0}
        s1_to_sec = {s1: sec for sec, s1 in _SEC_TO_S1.items()}

        rows = bind.execute(
            sa.text(
                "SELECT id, owner_l1_id, key, responsible_agent_profile_id, instructions, sort_order "
                "FROM admin_views WHERE owner_l1_id IS NOT NULL"
            )
        ).fetchall()
        by_s1: dict = {}
        for vid, oid, key, responsible, instructions, so in rows:
            by_s1.setdefault(oid, []).append((key, responsible, instructions, so))

        for s1_id, view_rows in by_s1.items():
            sec_id = s1_to_sec.get(s1_id)
            if not sec_id:
                continue
            agent = None
            views_payload: dict = {}
            for key, responsible, instructions, so in view_rows:
                if so == 0 and responsible and responsible != seed_default.get(s1_id):
                    agent = responsible
                if instructions and str(instructions).strip():
                    views_payload[key] = {"sidebar_body": instructions}
            if agent is None and not views_payload:
                continue
            bind.execute(
                sa.text(
                    "INSERT INTO admin_section_overrides (section_id, agent_profile_id, views) "
                    "VALUES (:sid, :agent, CAST(:views AS JSONB)) ON CONFLICT (section_id) DO NOTHING"
                ),
                {"sid": sec_id, "agent": agent, "views": _json_dumps(views_payload) if views_payload else None},
            )

    for table in ("admin_views", "admin_sections_l3", "admin_sections_l2", "admin_sections_l1", "admin_section_groups"):
        if inspector.has_table(table):
            op.drop_table(table)
    for prefix in ("vw", "s3", "s2", "s1", "grp"):
        op.execute(sa.text(f"DROP SEQUENCE IF EXISTS {prefix}_id_seq"))
