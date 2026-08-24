"""
Generación automática de IDs prefijados para todas las tablas de carrera.

Formato: {PREFIX}-{n}  ej. "ach-1", "cmp-42", "vac-7"
El prefijo identifica la tabla; el consecutivo es independiente por tabla.

Uso en cada modelo:
    from services.id_generator import register_id_listener
    register_id_listener(Achievement, "ach")
"""
from sqlalchemy import event, text

# Mapa canónico tabla → prefijo (fuente de verdad)
TABLE_PREFIXES: dict[str, str] = {
    "achievements":               "ach",
    "applications":               "apl",
    "application_interactions":   "ain",
    "bedrock_conversations":      "bco",
    "bedrock_conversation_messages": "bcm",
    "bedrock_custom_tools":       "bct",
    "bedrock_tasks":              "btk",
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
}


def _seq_name(table_name: str) -> str:
    prefix = TABLE_PREFIXES[table_name]
    return f"{prefix}_id_seq"


def register_id_listener(model_class, prefix: str) -> None:
    """Registra el evento before_insert para asignar el ID prefijado."""
    table_name = model_class.__tablename__

    @event.listens_for(model_class, "before_insert")
    def _assign_id(mapper, connection, target):
        if not target.id:
            seq = _seq_name(table_name)
            n = connection.execute(text(f"SELECT nextval('{seq}')")).scalar()
            target.id = f"{prefix}-{n}"
