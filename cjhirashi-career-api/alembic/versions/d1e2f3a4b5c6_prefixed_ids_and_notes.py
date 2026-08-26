"""Prefixed string IDs for all business tables and add notes field.

Strategy
--------
1. Drop ALL FK constraints in the public schema (dynamic query).
2. For each business table:
   a. Seed a PostgreSQL sequence from the current max(id).
   b. ALTER COLUMN id TYPE VARCHAR(20) USING '<prefix>-' || id::text
   c. Set column DEFAULT to use the sequence.
3. For each FK column in each table:
   ALTER COLUMN <col> TYPE VARCHAR(20) USING '<ref_prefix>-' || <col>::text
4. Add TEXT 'notes' column to tables that need it.
5. Fix audit_logs.resource_id and events.entity_id to VARCHAR(100).

Downgrade is intentionally not supported.

Revision ID: d1e2f3a4b5c6
Revises: c2d3e4f5a6b7
Create Date: 2026-08-24
"""
from alembic import op
import sqlalchemy as sa

revision = "d1e2f3a4b5c6"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None

# (db_table_name, prefix)
BUSINESS_TABLES: list[tuple[str, str]] = [
    ("users",                       "usr"),
    ("identity",                    "idn"),
    ("work_history",                "wkh"),
    ("target_roles",                "trl"),
    ("networking_contacts",         "nwc"),
    ("projects",                    "prj"),
    ("competencies",                "cmp"),
    ("differentiators",             "dif"),
    ("vacancies",                   "vac"),
    ("role_narratives",             "rna"),
    ("career_reviews",              "crv"),
    ("certifications",              "crt"),
    ("fit_scoring_factors",         "fsf"),
    ("github_profile",              "ghp"),
    ("identity_reflections",        "idr"),
    ("linkedin_connections",        "lnc"),
    ("linkedin_posts",              "lnp"),
    ("linkedin_profile",            "lnr"),
    ("market_segments",             "mks"),
    ("networking_activities",       "nwa"),
    ("operational_methodologies",   "opm"),
    ("pdf_output_templates",        "pdt"),
    ("portal_about",                "pab"),
    ("portal_contact",              "pco"),
    ("portal_home",                 "phm"),
    ("tags",                        "tag"),
    ("file_uploads",                "flu"),
    ("role_gap_analysis",           "rga"),
    ("search_plans",                "spl"),
    ("target_companies",            "tco"),
    ("achievements",                "ach"),
    ("star_stories",                "sts"),
    ("cv_versions",                 "cvv"),
    ("cover_letter_versions",       "clv"),
    ("applications",                "apl"),
    ("application_interactions",    "ain"),
    ("interviews",                  "ivw"),
    ("contact_interactions",        "cni"),
    ("publications",                "pub"),
    ("refresh_tokens",              "rtk"),
    ("user_sessions",               "uss"),
    ("bedrock_conversations",       "bco"),
    ("bedrock_conversation_messages", "bcm"),
    ("bedrock_tasks",               "btk"),
    ("bedrock_custom_tools",        "bct"),
]

# (db_table_name, fk_col_name, ref_prefix)
FK_COLS: list[tuple[str, str, str]] = [
    ("identity",                    "user_id",              "usr"),
    ("work_history",                "user_id",              "usr"),
    ("target_roles",                "user_id",              "usr"),
    ("networking_contacts",         "user_id",              "usr"),
    ("projects",                    "user_id",              "usr"),
    ("competencies",                "user_id",              "usr"),
    ("differentiators",             "user_id",              "usr"),
    ("vacancies",                   "user_id",              "usr"),
    ("role_narratives",             "user_id",              "usr"),
    ("role_narratives",             "target_role_id",       "trl"),
    ("career_reviews",              "user_id",              "usr"),
    ("certifications",              "user_id",              "usr"),
    ("certifications",              "related_competency_id","cmp"),
    ("fit_scoring_factors",         "user_id",              "usr"),
    ("github_profile",              "user_id",              "usr"),
    ("identity_reflections",        "user_id",              "usr"),
    ("linkedin_connections",        "user_id",              "usr"),
    ("linkedin_posts",              "user_id",              "usr"),
    ("linkedin_profile",            "user_id",              "usr"),
    ("market_segments",             "user_id",              "usr"),
    ("networking_activities",       "user_id",              "usr"),
    ("operational_methodologies",   "user_id",              "usr"),
    ("pdf_output_templates",        "user_id",              "usr"),
    ("portal_about",                "user_id",              "usr"),
    ("portal_contact",              "user_id",              "usr"),
    ("portal_home",                 "user_id",              "usr"),
    ("tags",                        "user_id",              "usr"),
    ("file_uploads",                "user_id",              "usr"),
    ("role_gap_analysis",           "user_id",              "usr"),
    ("role_gap_analysis",           "target_role_id",       "trl"),
    ("search_plans",                "user_id",              "usr"),
    ("search_plans",                "target_role_id",       "trl"),
    ("target_companies",            "user_id",              "usr"),
    ("target_companies",            "best_fit_role_id",     "trl"),
    ("target_companies",            "weak_tie_contact_id",  "nwc"),
    ("achievements",                "user_id",              "usr"),
    ("achievements",                "work_history_id",      "wkh"),
    ("star_stories",                "user_id",              "usr"),
    ("star_stories",                "achievement_id",       "ach"),
    ("cv_versions",                 "user_id",              "usr"),
    ("cv_versions",                 "target_role_id",       "trl"),
    ("cover_letter_versions",       "user_id",              "usr"),
    ("cover_letter_versions",       "target_role_id",       "trl"),
    ("cover_letter_versions",       "target_vacancy_id",    "vac"),
    ("applications",                "user_id",              "usr"),
    ("applications",                "vacancy_id",           "vac"),
    ("applications",                "cv_version_id",        "cvv"),
    ("applications",                "cover_letter_version_id", "clv"),
    ("applications",                "recruiter_contact_id", "nwc"),
    ("application_interactions",    "user_id",              "usr"),
    ("application_interactions",    "application_id",       "apl"),
    ("interviews",                  "user_id",              "usr"),
    ("interviews",                  "application_id",       "apl"),
    ("interviews",                  "narrative_used_id",    "rna"),
    ("contact_interactions",        "user_id",              "usr"),
    ("contact_interactions",        "contact_id",           "nwc"),
    ("contact_interactions",        "related_vacancy_id",   "vac"),
    ("publications",                "user_id",              "usr"),
    ("publications",                "related_project_id",   "prj"),
    ("refresh_tokens",              "user_id",              "usr"),
    ("user_sessions",               "user_id",              "usr"),
    ("bedrock_conversations",       "user_id",              "usr"),
    ("bedrock_conversation_messages","conversation_id",     "bco"),
    ("bedrock_tasks",               "user_id",              "usr"),
]

NOTES_TABLES = {
    "identity", "work_history", "target_roles", "networking_contacts",
    "projects", "competencies", "differentiators", "vacancies",
    "role_narratives", "career_reviews", "certifications", "fit_scoring_factors",
    "github_profile", "identity_reflections", "linkedin_connections",
    "linkedin_posts", "linkedin_profile", "market_segments",
    "networking_activities", "operational_methodologies", "pdf_output_templates",
    "portal_about", "portal_contact", "portal_home", "tags", "file_uploads",
    "role_gap_analysis", "search_plans", "target_companies", "achievements",
    "star_stories", "cv_versions", "cover_letter_versions", "applications",
    "application_interactions", "interviews", "contact_interactions",
    "publications", "bedrock_tasks",
}


def upgrade() -> None:
    conn = op.get_bind()

    # ── 0. Drop dependent views ────────────────────────────────────────────
    conn.execute(sa.text("DROP VIEW IF EXISTS search_metrics_view"))

    # ── 1. Drop ALL FK constraints in public schema ────────────────────────
    conn.execute(sa.text("""
        DO $$
        DECLARE r RECORD;
        BEGIN
            FOR r IN (
                SELECT tc.table_name, tc.constraint_name
                FROM information_schema.table_constraints tc
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public'
            ) LOOP
                EXECUTE 'ALTER TABLE ' || quote_ident(r.table_name)
                     || ' DROP CONSTRAINT ' || quote_ident(r.constraint_name);
            END LOOP;
        END $$;
    """))

    # ── 2. Convert each PK: seed sequence, ALTER TYPE, set default ─────────
    for table, prefix in BUSINESS_TABLES:
        seq = f"{prefix}_id_seq"
        # Seed sequence from current max (while id is still integer)
        conn.execute(sa.text(
            f"CREATE SEQUENCE IF NOT EXISTS {seq} START 1"
        ))
        conn.execute(sa.text(
            f"SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, false)"
        ))
        # Convert PK column
        conn.execute(sa.text(
            f"ALTER TABLE {table} ALTER COLUMN id TYPE VARCHAR(20) "
            f"USING '{prefix}-' || id::text"
        ))
        # Set default so future INSERTs auto-assign the prefixed ID
        conn.execute(sa.text(
            f"ALTER TABLE {table} ALTER COLUMN id "
            f"SET DEFAULT '{prefix}-' || nextval('{seq}')::text"
        ))

    # ── 3. Convert FK columns ─────────────────────────────────────────────
    for table, col, ref_prefix in FK_COLS:
        # Check if column is nullable or not (affects USING behaviour on NULLs)
        conn.execute(sa.text(
            f"ALTER TABLE {table} ALTER COLUMN {col} TYPE VARCHAR(20) "
            f"USING CASE WHEN {col} IS NULL THEN NULL "
            f"           ELSE '{ref_prefix}-' || {col}::text END"
        ))

    # ── 4. Add soft-ref columns (no ForeignKey() constraint) ─────────────
    # cv_versions.file_upload_id and cover_letter_versions.file_upload_id
    for table in ("cv_versions", "cover_letter_versions"):
        try:
            conn.execute(sa.text(
                f"ALTER TABLE {table} ALTER COLUMN file_upload_id TYPE VARCHAR(20) "
                f"USING CASE WHEN file_upload_id IS NULL THEN NULL "
                f"           ELSE 'flu-' || file_upload_id::text END"
            ))
        except Exception:
            pass  # column may not exist

    # ── 5. Add 'notes' TEXT column ─────────────────────────────────────────
    for table in NOTES_TABLES:
        conn.execute(sa.text(
            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS notes TEXT"
        ))

    # ── 6. Fix audit_logs.resource_id and events.entity_id ────────────────
    conn.execute(sa.text(
        "ALTER TABLE audit_logs ALTER COLUMN resource_id TYPE VARCHAR(100) "
        "USING resource_id::text"
    ))
    conn.execute(sa.text(
        "ALTER TABLE events ALTER COLUMN entity_id TYPE VARCHAR(100) "
        "USING entity_id::text"
    ))

    # ── 7. Recreate dependent views (with updated column types) ────────────
    conn.execute(sa.text("""
        CREATE VIEW search_metrics_view AS
        SELECT
            a.user_id,
            DATE_TRUNC('week', a.applied_at)::date AS week_start,
            COUNT(*) AS applications_sent,
            COUNT(*) FILTER (WHERE a.current_status <> 'applied') AS responses_received,
            ROUND(
                100.0 * COUNT(*) FILTER (WHERE a.current_status <> 'applied')::numeric
                / NULLIF(COUNT(*), 0)::numeric, 2
            ) AS response_rate_percentage,
            COUNT(DISTINCT i.id) AS interviews_scheduled,
            COUNT(*) FILTER (WHERE a.current_status = 'offer') AS offers,
            COUNT(*) FILTER (WHERE a.current_status = 'rejected') AS rejections
        FROM applications a
        LEFT JOIN interviews i ON i.application_id = a.id
        GROUP BY a.user_id, DATE_TRUNC('week', a.applied_at)
    """))


def downgrade() -> None:
    raise NotImplementedError("Downgrade not supported for this migration.")
