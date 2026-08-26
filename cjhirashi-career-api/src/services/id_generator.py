"""
Generación automática de IDs prefijados para todas las tablas de carrera.

Formato: {PREFIX}-{n}  ej. "ach-1", "cmp-42", "vac-7"
El prefijo identifica la tabla; el consecutivo es independiente por tabla.

Uso en cada modelo:
    from services.id_generator import register_id_listener
    register_id_listener(Achievement, "ach")
"""
from sqlalchemy import event, text

# ============================================================================
# Registro de prefijos
# ============================================================================

# Mapa canónico tabla → prefijo (fuente de verdad)
TABLE_PREFIXES: dict[str, str] = {
    "achievements":               "ach",
    "applications":               "apl",
    "application_interactions":   "ain",
    "bedrock_conversations":      "bco",
    "bedrock_conversation_messages": "bcm",
    "bedrock_custom_tools":       "bct",
    "bedrock_tasks":              "btk",
    "user_notifications":         "ntf",
    "career_reviews":             "crv",
    "certifications":             "crt",
    "competencies":               "cmp",
    "contact_interactions":       "cni",
    "cover_letter_versions":      "clv",
    "cv_versions":                "cvv",
    "differentiators":            "dif",
    "file_uploads":               "flu",
    "fit_scoring_factors":        "fsf",
    "github_profile":             "ghp",
    "identity":                   "idn",
    "personal_profile":           "psp",
    "identity_reflections":       "idr",
    "interviews":                 "ivw",
    "linkedin_connections":       "lnc",
    "linkedin_posts":             "lnp",
    "linkedin_profile":           "lnr",
    "market_segments":            "mks",
    "networking_activities":      "nwa",
    "networking_contacts":        "nwc",
    "operational_methodologies":  "opm",
    "pdf_output_templates":       "pdt",
    "pdf_template_styles":        "pds",
    "portal_about":               "pab",
    "portal_contact":             "pco",
    "portal_home":                "phm",
    "projects":                   "prj",
    "publications":               "pub",
    "refresh_tokens":             "rtk",
    "role_gap_analysis":          "rga",
    "role_narratives":            "rna",
    "search_plans":               "spl",
    "star_stories":               "sts",
    "tags":                       "tag",
    "target_companies":           "tco",
    "target_roles":               "trl",
    "users":                      "usr",
    "user_sessions":              "uss",
    "vacancies":                  "vac",
    "work_history":               "wkh",
    # Catálogo de agentes (IDs asignados en código, no hay secuencia PG).
    "agent_profiles":             "agent",
}


def prefix_for_key(key: str) -> str | None:
    """Resuelve prefijo desde resource_key (achievements, cv-versions) o nombre de tabla."""
    normalized = key.replace("-", "_")
    return TABLE_PREFIXES.get(normalized)


def normalize_prefixed_id(key: str, raw_id) -> str:
    """Convierte un id crudo al formato prefijado (ej. 17 → ach-17)."""
    if isinstance(raw_id, str):
        stripped = raw_id.strip()
        if "-" in stripped:
            return stripped
        if stripped.isdigit():
            prefix = prefix_for_key(key)
            if prefix:
                return f"{prefix}-{stripped}"
        return stripped
    if isinstance(raw_id, int):
        prefix = prefix_for_key(key)
        if prefix:
            return f"{prefix}-{raw_id}"
    return str(raw_id)


def _seq_name(table_name: str) -> str:
    prefix = TABLE_PREFIXES[table_name]
    return f"{prefix}_id_seq"


# ============================================================================
# Listener de inserción
# ============================================================================

def register_id_listener(model_class, prefix: str) -> None:
    """Registra el evento before_insert para asignar el ID prefijado."""
    table_name = model_class.__tablename__

    # ============================================================================
    # Generación de IDs
    # ============================================================================

    @event.listens_for(model_class, "before_insert")
    def _assign_id(mapper, connection, target):
        if not target.id:
            seq = _seq_name(table_name)
            n = connection.execute(text(f"SELECT nextval('{seq}')")).scalar()
            target.id = f"{prefix}-{n}"
