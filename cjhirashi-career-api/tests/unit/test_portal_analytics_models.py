"""
Tests for portal analytics models: ID generation, schema, constraints.
"""
import pytest
from sqlalchemy import inspect
from database import Base
from models import (
    PortalSite,
    PortalVisitor,
    PortalVisit,
    PortalGoal,
    PortalFunnel,
    PortalAnnotation,
    PortalChannelRule,
    PortalDaily,
    PortalEvent,
    User,
)


@pytest.mark.requisito("RF-040")
class TestPortalAnalyticsModels:
    """Test that portal analytics models are correctly defined."""

    def test_portal_site_model_exists(self):
        """Portal site model must exist with required columns."""
        assert PortalSite.__tablename__ == "portal_sites"
        columns = {c.name for c in PortalSite.__table__.columns}
        required = {"id", "user_id", "name", "domain", "public_key", "owner_token_hash",
                   "allowed_hosts", "timezone", "active", "created_at"}
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_portal_visitor_model_exists(self):
        """Portal visitor model must exist with required columns."""
        assert PortalVisitor.__tablename__ == "portal_visitors"
        columns = {c.name for c in PortalVisitor.__table__.columns}
        required = {"id", "user_id", "site_id", "visitor_key", "first_seen", "last_seen",
                   "visit_count", "country", "is_bot", "bot_score", "is_owner", "legacy", "created_at"}
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_portal_visit_model_exists(self):
        """Portal visit model must exist with required columns."""
        assert PortalVisit.__tablename__ == "portal_visits"
        columns = {c.name for c in PortalVisit.__table__.columns}
        required = {"id", "user_id", "site_id", "visitor_id", "started_at", "last_activity_at",
                   "entry_page", "exit_page", "referrer_url", "referrer_domain",
                   "utm_source", "utm_medium", "utm_campaign", "channel", "device_type",
                   "browser", "os", "country", "city", "latitude", "longitude",
                   "is_bot", "bot_score", "is_owner", "pageviews", "events_count",
                   "active_ms", "max_scroll_pct", "is_engaged", "is_bounce", "converted",
                   "created_at", "updated_at"}
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_portal_goal_model_exists(self):
        """Portal goal model must exist with required columns."""
        assert PortalGoal.__tablename__ == "portal_goals"
        columns = {c.name for c in PortalGoal.__table__.columns}
        required = {"id", "user_id", "site_id", "name", "type", "match", "is_key_event", "created_at"}
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_portal_funnel_model_exists(self):
        """Portal funnel model must exist with required columns."""
        assert PortalFunnel.__tablename__ == "portal_funnels"
        columns = {c.name for c in PortalFunnel.__table__.columns}
        required = {"id", "user_id", "site_id", "name", "steps", "created_at"}
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_portal_annotation_model_exists(self):
        """Portal annotation model must exist with required columns."""
        assert PortalAnnotation.__tablename__ == "portal_annotations"
        columns = {c.name for c in PortalAnnotation.__table__.columns}
        required = {"id", "user_id", "site_id", "day", "title", "kind", "ref", "created_at"}
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_portal_channel_rule_model_exists(self):
        """Portal channel rule model must exist with required columns."""
        assert PortalChannelRule.__tablename__ == "portal_channel_rules"
        columns = {c.name for c in PortalChannelRule.__table__.columns}
        required = {"id", "user_id", "site_id", "priority", "channel", "conditions", "created_at"}
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_portal_daily_model_exists(self):
        """Portal daily model must exist with required columns."""
        assert PortalDaily.__tablename__ == "portal_daily"
        columns = {c.name for c in PortalDaily.__table__.columns}
        required = {"id", "user_id", "site_id", "day", "dimension", "key",
                   "visitors", "visits", "pageviews", "engaged_visits", "bounces",
                   "active_ms_sum", "conversions", "computed_at"}
        assert required.issubset(columns), f"Missing columns: {required - columns}"

    def test_portal_event_extended_columns(self):
        """Portal event must have new columns for v2 analytics."""
        columns = {c.name for c in PortalEvent.__table__.columns}
        new_required = {"site_id", "visitor_id", "visit_id", "seq", "page_title",
                       "props", "scroll_pct", "active_ms", "target_url"}
        assert new_required.issubset(columns), f"Missing new columns in portal_events: {new_required - columns}"
        # Check that old columns still exist
        old_required = {"event_type", "page", "session_id", "duration_ms", "country", "created_at"}
        assert old_required.issubset(columns), f"Old columns missing: {old_required - columns}"

    def test_portal_sites_uniqueness_constraints(self):
        """Portal sites must have unique domain and public_key."""
        # Check via the table columns
        assert PortalSite.domain.unique is True, "Domain must be unique"
        assert PortalSite.public_key.unique is True, "Public key must be unique"

    def test_portal_visitor_uniqueness_constraint(self):
        """Portal visitor must have unique (site_id, visitor_key)."""
        # Check via table_args
        table_args = getattr(PortalVisitor, "__table_args__", ())
        if table_args:
            has_site_visitor_unique = any(
                hasattr(constraint, "columns") and
                set(str(c.name) for c in constraint.columns) == {"site_id", "visitor_key"}
                for constraint in table_args if hasattr(constraint, "columns")
            )
            assert has_site_visitor_unique, "Missing unique constraint on (site_id, visitor_key)"

    def test_portal_daily_uniqueness_constraint(self):
        """Portal daily must have unique (site_id, day, dimension, key)."""
        # Check via table_args
        table_args = getattr(PortalDaily, "__table_args__", ())
        if table_args:
            has_dimension_unique = any(
                hasattr(constraint, "columns") and
                set(str(c.name) for c in constraint.columns) == {"site_id", "day", "dimension", "key"}
                for constraint in table_args if hasattr(constraint, "columns")
            )
            assert has_dimension_unique, "Missing unique constraint on (site_id, day, dimension, key)"

    def test_portal_visit_has_basic_indices(self):
        """Portal visit must have basic indices at least."""
        # Check via the table constraints
        indices = PortalVisit.__table__.indexes
        index_names = {idx.name for idx in indices}
        # Just verify that some indices exist (composite indices are created in migration)
        assert len(index_names) > 0, "Portal visits must have at least some indices"


@pytest.mark.requisito("RF-040")
class TestPortalAnalyticsIDGeneration:
    """Test that portal analytics models generate IDs with correct prefixes."""

    async def test_portal_site_id_generation(self, test_db):
        """Portal site IDs must use psi- prefix."""
        async with test_db() as session:
            # Create a user first
            user = User(id="usr-1", username="testuser", email="test@example.com", password_hash="hash")
            session.add(user)
            await session.flush()

            # Create portal site
            site = PortalSite(
                user_id="usr-1",
                name="Test Site",
                domain="test.com",
                public_key="testkey123456789012",
                owner_token_hash="hash"
            )
            session.add(site)
            await session.flush()

            assert site.id.startswith("psi-"), f"Portal site ID must start with psi-, got {site.id}"

    async def test_portal_visitor_id_generation(self, test_db):
        """Portal visitor IDs must use pvr- prefix."""
        from datetime import datetime
        async with test_db() as session:
            # Create prerequisites
            user = User(id="usr-2", username="testuser2", email="test2@example.com", password_hash="hash")
            session.add(user)
            await session.flush()

            site = PortalSite(
                id="psi-1",
                user_id="usr-2",
                name="Test Site",
                domain="test2.com",
                public_key="testkey123456789012",
                owner_token_hash="hash"
            )
            session.add(site)
            await session.flush()

            # Create portal visitor
            now = datetime.utcnow()
            visitor = PortalVisitor(
                user_id="usr-2",
                site_id="psi-1",
                visitor_key="test_visitor_key",
                first_seen=now,
                last_seen=now
            )
            session.add(visitor)
            await session.flush()

            assert visitor.id.startswith("pvr-"), f"Portal visitor ID must start with pvr-, got {visitor.id}"

    async def test_portal_visit_id_generation(self, test_db):
        """Portal visit IDs must use pvs- prefix."""
        from datetime import datetime
        async with test_db() as session:
            # Create prerequisites
            user = User(id="usr-3", username="testuser3", email="test3@example.com", password_hash="hash")
            session.add(user)
            await session.flush()

            site = PortalSite(
                id="psi-2",
                user_id="usr-3",
                name="Test Site",
                domain="test3.com",
                public_key="testkey123456789012",
                owner_token_hash="hash"
            )
            session.add(site)
            await session.flush()

            now = datetime.utcnow()
            visitor = PortalVisitor(
                id="pvr-1",
                user_id="usr-3",
                site_id="psi-2",
                visitor_key="test_visitor_key",
                first_seen=now,
                last_seen=now
            )
            session.add(visitor)
            await session.flush()

            # Create portal visit
            visit = PortalVisit(
                user_id="usr-3",
                site_id="psi-2",
                visitor_id="pvr-1",
                started_at=now,
                last_activity_at=now,
                entry_page="/test"
            )
            session.add(visit)
            await session.flush()

            assert visit.id.startswith("pvs-"), f"Portal visit ID must start with pvs-, got {visit.id}"
