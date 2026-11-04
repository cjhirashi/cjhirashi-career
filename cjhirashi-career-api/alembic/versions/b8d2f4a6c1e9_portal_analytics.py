"""portal_analytics - Portal analytics tables: sites, visitors, visits, goals, funnels, annotations, channel rules, daily rollups.
Adds multi-site analytics framework with raw event tracking and lazy daily aggregation.

Revision ID: b8d2f4a6c1e9
Revises: a7c1e9d2f4b8
"""
from typing import Sequence, Union
import hashlib
import json
import os
import secrets

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b8d2f4a6c1e9"
down_revision: Union[str, None] = "a7c1e9d2f4b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sequences for all new tables
    op.execute("CREATE SEQUENCE IF NOT EXISTS psi_id_seq START 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS pvr_id_seq START 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS pvs_id_seq START 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS pgl_id_seq START 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS pfn_id_seq START 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS pan_id_seq START 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS pcr_id_seq START 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS pdy_id_seq START 1")

    # Create portal_sites table
    op.create_table(
        "portal_sites",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("public_key", sa.String(length=24), nullable=False),
        sa.Column("owner_token_hash", sa.String(length=64), nullable=False),
        sa.Column("allowed_hosts", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("timezone", sa.String(length=50), nullable=False, server_default="America/Mexico_City"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain", name="uix_portal_sites_domain"),
        sa.UniqueConstraint("public_key", name="uix_portal_sites_public_key"),
    )
    op.create_index("ix_portal_sites_user_id", "portal_sites", ["user_id"])
    op.create_index("ix_portal_sites_domain", "portal_sites", ["domain"])
    op.create_index("ix_portal_sites_public_key", "portal_sites", ["public_key"])
    op.create_index("ix_portal_sites_created_at", "portal_sites", ["created_at"])

    # Create portal_visitors table
    op.create_table(
        "portal_visitors",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("site_id", sa.String(length=20), nullable=False),
        sa.Column("visitor_key", sa.String(length=64), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("visit_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_referrer_domain", sa.String(length=255), nullable=True),
        sa.Column("first_channel", sa.String(length=50), nullable=True),
        sa.Column("first_utm_source", sa.String(length=255), nullable=True),
        sa.Column("first_utm_medium", sa.String(length=255), nullable=True),
        sa.Column("first_utm_campaign", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("is_bot", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("bot_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_owner", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("legacy", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["portal_sites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("site_id", "visitor_key", name="uix_portal_visitors_site_visitor"),
    )
    op.create_index("ix_portal_visitors_user_id", "portal_visitors", ["user_id"])
    op.create_index("ix_portal_visitors_site_id", "portal_visitors", ["site_id"])
    op.create_index("ix_portal_visitors_visitor_key", "portal_visitors", ["visitor_key"])
    op.create_index("ix_portal_visitors_country", "portal_visitors", ["country"])
    op.create_index("ix_portal_visitors_created_at", "portal_visitors", ["created_at"])

    # Create portal_visits table
    op.create_table(
        "portal_visits",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("site_id", sa.String(length=20), nullable=False),
        sa.Column("visitor_id", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("entry_page", sa.String(length=500), nullable=False),
        sa.Column("exit_page", sa.String(length=500), nullable=True),
        sa.Column("referrer_url", sa.String(length=1024), nullable=True),
        sa.Column("referrer_domain", sa.String(length=255), nullable=True),
        sa.Column("utm_source", sa.String(length=255), nullable=True),
        sa.Column("utm_medium", sa.String(length=255), nullable=True),
        sa.Column("utm_campaign", sa.String(length=255), nullable=True),
        sa.Column("utm_content", sa.String(length=255), nullable=True),
        sa.Column("utm_term", sa.String(length=255), nullable=True),
        sa.Column("click_id_type", sa.String(length=50), nullable=True),
        sa.Column("channel", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("device_type", sa.String(length=50), nullable=True),
        sa.Column("browser", sa.String(length=100), nullable=True),
        sa.Column("browser_version", sa.String(length=50), nullable=True),
        sa.Column("os", sa.String(length=100), nullable=True),
        sa.Column("os_version", sa.String(length=50), nullable=True),
        sa.Column("screen_size", sa.String(length=50), nullable=True),
        sa.Column("language", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("timezone", sa.String(length=50), nullable=True),
        sa.Column("is_bot", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("bot_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bot_reasons", postgresql.JSONB(), nullable=True, server_default="[]"),
        sa.Column("is_owner", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_new_visitor", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("pageviews", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("events_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_scroll_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_engaged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_bounce", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("converted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("application_id", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["portal_sites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["visitor_id"], ["portal_visitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portal_visits_user_id", "portal_visits", ["user_id"])
    op.create_index("ix_portal_visits_site_id", "portal_visits", ["site_id"])
    op.create_index("ix_portal_visits_visitor_id", "portal_visits", ["visitor_id"])
    op.create_index("ix_portal_visits_created_at", "portal_visits", ["created_at"])
    op.create_index("ix_portal_visits_updated_at", "portal_visits", ["updated_at"])
    op.create_index("ix_portal_visits_site_started", "portal_visits", ["site_id", "started_at"])
    op.create_index("ix_portal_visits_visitor_activity", "portal_visits", ["visitor_id", "last_activity_at"], postgresql_ops={"last_activity_at": "DESC"})
    op.create_index("ix_portal_visits_site_channel_started", "portal_visits", ["site_id", "channel", "started_at"])
    op.create_index("ix_portal_visits_site_country_started", "portal_visits", ["site_id", "country", "started_at"])
    op.create_index("ix_portal_visits_application", "portal_visits", ["application_id"])

    # Create portal_goals table
    op.create_table(
        "portal_goals",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("site_id", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("match", postgresql.JSONB(), nullable=False),
        sa.Column("is_key_event", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["portal_sites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portal_goals_user_id", "portal_goals", ["user_id"])
    op.create_index("ix_portal_goals_site_id", "portal_goals", ["site_id"])
    op.create_index("ix_portal_goals_created_at", "portal_goals", ["created_at"])

    # Create portal_funnels table
    op.create_table(
        "portal_funnels",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("site_id", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("steps", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["portal_sites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portal_funnels_user_id", "portal_funnels", ["user_id"])
    op.create_index("ix_portal_funnels_site_id", "portal_funnels", ["site_id"])
    op.create_index("ix_portal_funnels_created_at", "portal_funnels", ["created_at"])

    # Create portal_annotations table
    op.create_table(
        "portal_annotations",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("site_id", sa.String(length=20), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("ref", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["portal_sites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portal_annotations_user_id", "portal_annotations", ["user_id"])
    op.create_index("ix_portal_annotations_site_id", "portal_annotations", ["site_id"])
    op.create_index("ix_portal_annotations_day", "portal_annotations", ["day"])
    op.create_index("ix_portal_annotations_created_at", "portal_annotations", ["created_at"])

    # Create portal_channel_rules table
    op.create_table(
        "portal_channel_rules",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("site_id", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("conditions", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["portal_sites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portal_channel_rules_user_id", "portal_channel_rules", ["user_id"])
    op.create_index("ix_portal_channel_rules_site_id", "portal_channel_rules", ["site_id"])
    op.create_index("ix_portal_channel_rules_created_at", "portal_channel_rules", ["created_at"])

    # Create portal_daily table
    op.create_table(
        "portal_daily",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.String(length=20), nullable=False),
        sa.Column("site_id", sa.String(length=20), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("dimension", sa.String(length=50), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("visitors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("visits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pageviews", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("engaged_visits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bounces", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_ms_sum", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conversions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["site_id"], ["portal_sites.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("site_id", "day", "dimension", "key", name="uix_portal_daily_dimension"),
    )
    op.create_index("ix_portal_daily_user_id", "portal_daily", ["user_id"])
    op.create_index("ix_portal_daily_site_id", "portal_daily", ["site_id"])
    op.create_index("ix_portal_daily_day", "portal_daily", ["day"])
    op.create_index("ix_portal_daily_computed_at", "portal_daily", ["computed_at"])

    # Add new columns to portal_events
    op.add_column("portal_events", sa.Column("site_id", sa.String(length=20), nullable=True))
    op.add_column("portal_events", sa.Column("visitor_id", sa.String(length=20), nullable=True))
    op.add_column("portal_events", sa.Column("visit_id", sa.String(length=20), nullable=True))
    op.add_column("portal_events", sa.Column("seq", sa.Integer(), nullable=True))
    op.add_column("portal_events", sa.Column("page_title", sa.String(length=500), nullable=True))
    op.add_column("portal_events", sa.Column("props", postgresql.JSONB(), nullable=True))
    op.add_column("portal_events", sa.Column("scroll_pct", sa.Integer(), nullable=True))
    op.add_column("portal_events", sa.Column("active_ms", sa.Integer(), nullable=True))
    op.add_column("portal_events", sa.Column("target_url", sa.String(length=1024), nullable=True))

    # Add foreign key constraints for portal_events new columns
    op.create_foreign_key("fk_portal_events_site_id", "portal_events", "portal_sites", ["site_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_portal_events_visitor_id", "portal_events", "portal_visitors", ["visitor_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_portal_events_visit_id", "portal_events", "portal_visits", ["visit_id"], ["id"], ondelete="CASCADE")

    # Add indices for portal_events new columns
    op.create_index("ix_portal_events_site_id", "portal_events", ["site_id"])
    op.create_index("ix_portal_events_visitor_id", "portal_events", ["visitor_id"])
    op.create_index("ix_portal_events_visit_id", "portal_events", ["visit_id"])
    op.create_index("ix_portal_events_site_created_at", "portal_events", ["site_id", "created_at"])
    op.create_index("ix_portal_events_visit_seq", "portal_events", ["visit_id", "seq"])
    op.create_index("ix_portal_events_visitor_created_at", "portal_events", ["visitor_id", "created_at"])

    conn = op.get_bind()
    site = _seed_defaults(conn)
    if site:
        _backfill_legacy(conn, *site)


def _next_id(conn, prefix: str) -> str:
    query = sa.text("SELECT nextval('" + prefix + "_id_seq')")
    return prefix + "-" + str(conn.execute(query).scalar())


def _seed_defaults(conn) -> None:
    """Siembra el sitio del portafolio, sus reglas de canal y sus metas.

    El dueño se resuelve en este orden: PUBLIC_PORTAL_USER_ID (si existe en
    users), el usuario con más eventos en portal_events, el primer usuario.
    """
    owner_id = None
    configured = os.environ.get("PUBLIC_PORTAL_USER_ID")
    if configured:
        owner_id = conn.execute(
            sa.text("SELECT id FROM users WHERE id = :id"), {"id": configured}
        ).scalar()
    if owner_id is None:
        owner_id = conn.execute(
            sa.text("SELECT user_id FROM portal_events GROUP BY user_id ORDER BY count(*) DESC LIMIT 1")
        ).scalar()
    if owner_id is None:
        owner_id = conn.execute(sa.text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")).scalar()
    if owner_id is None:
        return None

    public_key = secrets.token_urlsafe(18)  # 24 caracteres
    owner_token = secrets.token_urlsafe(32)
    owner_token_hash = hashlib.sha256(owner_token.encode()).hexdigest()
    site_id = _next_id(conn, "psi")

    conn.execute(
        sa.text(
            "INSERT INTO portal_sites (id, user_id, name, domain, public_key, owner_token_hash,"
            " allowed_hosts, timezone, active)"
            " VALUES (:id, :user_id, :name, :domain, :public_key, :hash,"
            " CAST(:hosts AS jsonb), :tz, true)"
        ),
        {
            "id": site_id,
            "user_id": owner_id,
            "name": "cjhirashi.com",
            "domain": "cjhirashi.com",
            "public_key": public_key,
            "hash": owner_token_hash,
            "hosts": json.dumps(["cjhirashi.com", "www.cjhirashi.com"]),
            "tz": "America/Mexico_City",
        },
    )
    # El token del dueño solo existe aquí: se imprime una vez y no se guarda en claro.
    print(f"\nOWNER_TOKEN={owner_token}\nPORTAL_SITE_ID={site_id}\nPORTAL_PUBLIC_KEY={public_key}\n")

    social = [
        "linkedin.com", "lnkd.in", "github.com", "twitter.com", "x.com", "t.co", "facebook.com",
        "instagram.com", "youtube.com", "reddit.com", "medium.com",
    ]
    # Cada regla exige TODAS sus condiciones; un canal con alternativas usa varias reglas.
    rules = [
        ("Application", {"utm_medium_in": ["postulacion", "application"]}),
        ("Email", {"utm_medium_in": ["email", "e-mail", "e_mail"]}),
        ("Email", {"utm_source_in": ["email", "e-mail", "e_mail", "newsletter"]}),
        ("Paid", {"utm_medium_in": ["cpc", "ppc", "paid", "paidsearch"]}),
        ("Organic Social", {"utm_medium_in": ["social", "social-network", "social-media"]}),
        ("Organic Social", {"referrer_domain_in": social}),
        ("Organic Search", {"utm_medium_in": ["organic"]}),
        ("Organic Search", {"referrer_domain_regex": r"(^|\.)(google|bing|duckduckgo|yahoo|ecosia|baidu|yandex|brave)\."}),
        ("Referral", {"referrer_present": True, "referrer_domain_not_in": ["cjhirashi.com"]}),
        ("Direct", {"no_referrer": True, "no_utm": True}),
        ("Unknown", {}),
    ]
    for priority, (channel, conditions) in enumerate(rules):
        rule_id = _next_id(conn, "pcr")
        conn.execute(
            sa.text(
                "INSERT INTO portal_channel_rules (id, user_id, site_id, priority, channel, conditions)"
                " VALUES (:id, :user_id, :site_id, :priority, :channel, CAST(:conditions AS jsonb))"
            ),
            {
                "id": rule_id, "user_id": owner_id, "site_id": site_id, "priority": priority,
                "channel": channel, "conditions": json.dumps(conditions),
            },
        )

    goals = [
        ("cv_download", "event", {"event_type": "download"}, True),
        ("contact_submit", "event", {"event_type": "form_submit"}, True),
        ("outbound_linkedin", "outbound", {"url_contains": "linkedin.com"}, True),
        ("outbound_github", "outbound", {"url_contains": "github.com"}, True),
        ("project_open", "page", {"path_prefix": "/projects/"}, False),
    ]
    for name, goal_type, match, is_key in goals:
        goal_id = _next_id(conn, "pgl")
        conn.execute(
            sa.text(
                "INSERT INTO portal_goals (id, user_id, site_id, name, type, match, is_key_event)"
                " VALUES (:id, :user_id, :site_id, :name, :type, CAST(:match AS jsonb), :is_key)"
            ),
            {
                "id": goal_id, "user_id": owner_id, "site_id": site_id, "name": name,
                "type": goal_type, "match": json.dumps(match), "is_key": is_key,
            },
        )
    return owner_id, site_id


_BOT_RE = "bot|crawl|spider|headless|curl|wget|python|httpclient|scrapy|slurp"


def _backfill_legacy(conn, owner_id: str, site_id: str) -> None:
    """Reconstruye visitantes y visitas desde los eventos v1 ya guardados.

    Un visitante por `session_id` (los eventos sin sesión son un visitante cada
    uno); dentro de un visitante, una visita nueva tras 30 min de hueco. Los
    datos de dispositivo y referrer no existían en v1 y quedan nulos; el canal
    es 'Unknown'. Los eventos conservan su contenido y solo ganan sus ids.
    """
    params = {"owner": owner_id, "site": site_id, "bot_re": _BOT_RE}

    conn.execute(sa.text("""
        CREATE TEMP TABLE tmp_legacy_ev ON COMMIT DROP AS
        SELECT id, created_at, event_type, page, duration_ms, user_agent, country, region, city,
               latitude, longitude, COALESCE(session_id, 'ev-' || id) AS vkey
        FROM portal_events WHERE site_id IS NULL AND user_id = :owner
    """), params)

    conn.execute(sa.text("""
        INSERT INTO portal_visitors (id, user_id, site_id, visitor_key, first_seen, last_seen,
                                     visit_count, first_channel, country, is_bot, bot_score, legacy)
        SELECT 'pvr-' || nextval('pvr_id_seq'), :owner, :site, vkey, first_seen, last_seen, 0, 'Unknown',
               country, is_bot, CASE WHEN is_bot THEN 80 ELSE 0 END, true
        FROM (
            SELECT vkey, min(created_at) AS first_seen, max(created_at) AS last_seen,
                   (array_agg(country ORDER BY created_at) FILTER (WHERE country IS NOT NULL))[1] AS country,
                   bool_or(user_agent ~* :bot_re) AS is_bot
            FROM tmp_legacy_ev GROUP BY vkey
        ) g
    """), params)

    conn.execute(sa.text("""
        CREATE TEMP TABLE tmp_legacy_map ON COMMIT DROP AS
        SELECT e.id AS event_id, v.id AS visitor_id, e.created_at, e.event_type, e.page, e.duration_ms,
               e.user_agent, e.country, e.region, e.city, e.latitude, e.longitude,
               SUM(new_visit) OVER (PARTITION BY v.id ORDER BY e.created_at, e.id) AS vno
        FROM (
            SELECT t.*, CASE WHEN t.created_at - lag(t.created_at) OVER (PARTITION BY t.vkey ORDER BY t.created_at, t.id)
                                  > interval '30 minutes' THEN 1 ELSE 0 END AS new_visit
            FROM tmp_legacy_ev t
        ) e
        JOIN portal_visitors v ON v.site_id = :site AND v.visitor_key = e.vkey
    """), params)

    conn.execute(sa.text("""
        CREATE TEMP TABLE tmp_legacy_visit ON COMMIT DROP AS
        SELECT 'pvs-' || nextval('pvs_id_seq') AS id, visitor_id, vno, started_at, last_activity_at,
               entry_page, exit_page, country, region, city, latitude, longitude, is_bot,
               pageviews, events_count, active_ms, converted
        FROM (
            SELECT visitor_id, vno,
                   min(created_at) AS started_at, max(created_at) AS last_activity_at,
                   (array_agg(page ORDER BY created_at, event_id))[1] AS entry_page,
                   (array_agg(page ORDER BY created_at DESC, event_id DESC))[1] AS exit_page,
                   (array_agg(country ORDER BY created_at) FILTER (WHERE country IS NOT NULL))[1] AS country,
                   (array_agg(region ORDER BY created_at) FILTER (WHERE region IS NOT NULL))[1] AS region,
                   (array_agg(city ORDER BY created_at) FILTER (WHERE city IS NOT NULL))[1] AS city,
                   (array_agg(latitude ORDER BY created_at) FILTER (WHERE latitude IS NOT NULL))[1] AS latitude,
                   (array_agg(longitude ORDER BY created_at) FILTER (WHERE longitude IS NOT NULL))[1] AS longitude,
                   bool_or(user_agent ~* :bot_re) AS is_bot,
                   count(*) FILTER (WHERE event_type = 'pageview') AS pageviews,
                   count(*) AS events_count,
                   COALESCE(sum(LEAST(duration_ms, 1800000)) FILTER (WHERE event_type = 'page_duration'), 0) AS active_ms,
                   bool_or(event_type IN ('download', 'form_submit')) AS converted
            FROM tmp_legacy_map GROUP BY visitor_id, vno
        ) g
    """), params)

    conn.execute(sa.text("""
        INSERT INTO portal_visits (id, user_id, site_id, visitor_id, started_at, last_activity_at, entry_page, exit_page,
            channel, country, region, city, latitude, longitude, is_bot, bot_score, is_new_visitor,
            pageviews, events_count, active_ms, is_engaged, is_bounce, converted)
        SELECT id, :owner, :site, visitor_id, started_at, last_activity_at, entry_page, exit_page,
               'Unknown', country, region, city, latitude, longitude, is_bot, CASE WHEN is_bot THEN 80 ELSE 0 END,
               vno = 1, pageviews, events_count, active_ms::int,
               (active_ms > 10000 OR pageviews >= 2 OR converted),
               NOT (active_ms > 10000 OR pageviews >= 2 OR converted), converted
        FROM tmp_legacy_visit
    """), params)

    conn.execute(sa.text("""
        UPDATE portal_events e
        SET site_id = :site, visitor_id = m.visitor_id, visit_id = lv.id, seq = m.seq
        FROM (SELECT event_id, visitor_id, vno,
                     row_number() OVER (PARTITION BY visitor_id, vno ORDER BY created_at, event_id) AS seq
              FROM tmp_legacy_map) m
        JOIN tmp_legacy_visit lv ON lv.visitor_id = m.visitor_id AND lv.vno = m.vno
        WHERE e.id = m.event_id
    """), params)

    conn.execute(sa.text("""
        UPDATE portal_visitors pv SET visit_count = c.n
        FROM (SELECT visitor_id, count(*) AS n FROM portal_visits WHERE site_id = :site GROUP BY visitor_id) c
        WHERE pv.id = c.visitor_id
    """), params)


def downgrade() -> None:
    # Drop indices and foreign keys from portal_events new columns
    op.drop_index("ix_portal_events_visitor_created_at", table_name="portal_events")
    op.drop_index("ix_portal_events_visit_seq", table_name="portal_events")
    op.drop_index("ix_portal_events_site_created_at", table_name="portal_events")
    op.drop_index("ix_portal_events_visitor_id", table_name="portal_events")
    op.drop_index("ix_portal_events_site_id", table_name="portal_events")

    op.drop_constraint("fk_portal_events_visit_id", "portal_events", type_="foreignkey")
    op.drop_constraint("fk_portal_events_visitor_id", "portal_events", type_="foreignkey")
    op.drop_constraint("fk_portal_events_site_id", "portal_events", type_="foreignkey")

    # Drop new columns from portal_events
    op.drop_column("portal_events", "target_url")
    op.drop_column("portal_events", "active_ms")
    op.drop_column("portal_events", "scroll_pct")
    op.drop_column("portal_events", "props")
    op.drop_column("portal_events", "page_title")
    op.drop_column("portal_events", "seq")
    op.drop_column("portal_events", "visit_id")
    op.drop_column("portal_events", "visitor_id")
    op.drop_column("portal_events", "site_id")

    # Drop portal_daily table and indices
    op.drop_index("ix_portal_daily_computed_at", table_name="portal_daily")
    op.drop_index("ix_portal_daily_day", table_name="portal_daily")
    op.drop_index("ix_portal_daily_site_id", table_name="portal_daily")
    op.drop_index("ix_portal_daily_user_id", table_name="portal_daily")
    op.drop_table("portal_daily")
    op.execute("DROP SEQUENCE IF EXISTS pdy_id_seq")

    # Drop portal_channel_rules table and indices
    op.drop_index("ix_portal_channel_rules_created_at", table_name="portal_channel_rules")
    op.drop_index("ix_portal_channel_rules_site_id", table_name="portal_channel_rules")
    op.drop_index("ix_portal_channel_rules_user_id", table_name="portal_channel_rules")
    op.drop_table("portal_channel_rules")
    op.execute("DROP SEQUENCE IF EXISTS pcr_id_seq")

    # Drop portal_annotations table and indices
    op.drop_index("ix_portal_annotations_created_at", table_name="portal_annotations")
    op.drop_index("ix_portal_annotations_day", table_name="portal_annotations")
    op.drop_index("ix_portal_annotations_site_id", table_name="portal_annotations")
    op.drop_index("ix_portal_annotations_user_id", table_name="portal_annotations")
    op.drop_table("portal_annotations")
    op.execute("DROP SEQUENCE IF EXISTS pan_id_seq")

    # Drop portal_funnels table and indices
    op.drop_index("ix_portal_funnels_created_at", table_name="portal_funnels")
    op.drop_index("ix_portal_funnels_site_id", table_name="portal_funnels")
    op.drop_index("ix_portal_funnels_user_id", table_name="portal_funnels")
    op.drop_table("portal_funnels")
    op.execute("DROP SEQUENCE IF EXISTS pfn_id_seq")

    # Drop portal_goals table and indices
    op.drop_index("ix_portal_goals_created_at", table_name="portal_goals")
    op.drop_index("ix_portal_goals_site_id", table_name="portal_goals")
    op.drop_index("ix_portal_goals_user_id", table_name="portal_goals")
    op.drop_table("portal_goals")
    op.execute("DROP SEQUENCE IF EXISTS pgl_id_seq")

    # Drop portal_visits table and indices
    op.drop_index("ix_portal_visits_application", table_name="portal_visits")
    op.drop_index("ix_portal_visits_site_country_started", table_name="portal_visits")
    op.drop_index("ix_portal_visits_site_channel_started", table_name="portal_visits")
    op.drop_index("ix_portal_visits_visitor_activity", table_name="portal_visits")
    op.drop_index("ix_portal_visits_site_started", table_name="portal_visits")
    op.drop_index("ix_portal_visits_updated_at", table_name="portal_visits")
    op.drop_index("ix_portal_visits_created_at", table_name="portal_visits")
    op.drop_index("ix_portal_visits_visitor_id", table_name="portal_visits")
    op.drop_index("ix_portal_visits_site_id", table_name="portal_visits")
    op.drop_index("ix_portal_visits_user_id", table_name="portal_visits")
    op.drop_table("portal_visits")
    op.execute("DROP SEQUENCE IF EXISTS pvs_id_seq")

    # Drop portal_visitors table and indices
    op.drop_index("ix_portal_visitors_created_at", table_name="portal_visitors")
    op.drop_index("ix_portal_visitors_country", table_name="portal_visitors")
    op.drop_index("ix_portal_visitors_visitor_key", table_name="portal_visitors")
    op.drop_index("ix_portal_visitors_site_id", table_name="portal_visitors")
    op.drop_index("ix_portal_visitors_user_id", table_name="portal_visitors")
    op.drop_table("portal_visitors")
    op.execute("DROP SEQUENCE IF EXISTS pvr_id_seq")

    # Drop portal_sites table and indices
    op.drop_index("ix_portal_sites_created_at", table_name="portal_sites")
    op.drop_index("ix_portal_sites_public_key", table_name="portal_sites")
    op.drop_index("ix_portal_sites_domain", table_name="portal_sites")
    op.drop_index("ix_portal_sites_user_id", table_name="portal_sites")
    op.drop_table("portal_sites")
    op.execute("DROP SEQUENCE IF EXISTS psi_id_seq")
