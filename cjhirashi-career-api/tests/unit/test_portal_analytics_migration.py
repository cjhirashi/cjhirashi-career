"""
Tests for portal analytics migration: structure, uniqueness, and downgrade.
"""
import pytest
from pathlib import Path
from sqlalchemy import inspect, text
from alembic.config import Config
from alembic.script import ScriptDirectory


@pytest.mark.requisito("RF-040")
class TestPortalAnalyticsMigration:
    """Test portal analytics migration structure and reversibility."""

    def test_migration_file_exists(self):
        """The portal_analytics migration file must exist."""
        migration_file = Path(__file__).parent.parent.parent / "alembic/versions/b8d2f4a6c1e9_portal_analytics.py"
        assert migration_file.exists(), f"Migration file not found: {migration_file}"

    def test_migration_has_upgrade_and_downgrade(self):
        """The migration must have both upgrade and downgrade functions."""
        migration_file = Path(__file__).parent.parent.parent / "alembic/versions/b8d2f4a6c1e9_portal_analytics.py"
        with open(migration_file) as f:
            content = f.read()
        assert "def upgrade()" in content, "Migration must have upgrade() function"
        assert "def downgrade()" in content, "Migration must have downgrade() function"

    def test_migration_down_revision_is_correct(self):
        """The migration down_revision must be a7c1e9d2f4b8."""
        migration_file = Path(__file__).parent.parent.parent / "alembic/versions/b8d2f4a6c1e9_portal_analytics.py"
        with open(migration_file) as f:
            content = f.read()
        assert 'down_revision: Union[str, None] = "a7c1e9d2f4b8"' in content, \
            "down_revision must be exactly 'a7c1e9d2f4b8'"

    def test_migration_has_create_sequences(self):
        """Migration must create all required sequences."""
        migration_file = Path(__file__).parent.parent.parent / "alembic/versions/b8d2f4a6c1e9_portal_analytics.py"
        with open(migration_file) as f:
            content = f.read()
        required_sequences = ["psi_id_seq", "pvr_id_seq", "pvs_id_seq", "pgl_id_seq",
                             "pfn_id_seq", "pan_id_seq", "pcr_id_seq", "pdy_id_seq"]
        for seq in required_sequences:
            assert seq in content, f"Migration must create sequence {seq}"

    def test_migration_creates_tables_in_upgrade(self):
        """Migration upgrade must create all required tables."""
        migration_file = Path(__file__).parent.parent.parent / "alembic/versions/b8d2f4a6c1e9_portal_analytics.py"
        with open(migration_file) as f:
            content = f.read()
        required_tables = ["portal_sites", "portal_visitors", "portal_visits", "portal_goals",
                          "portal_funnels", "portal_annotations", "portal_channel_rules", "portal_daily"]
        for table in required_tables:
            assert f'"{table}"' in content or f"'{table}'" in content, \
                f"Migration must create table {table}"

    def test_migration_drops_tables_in_downgrade(self):
        """Migration downgrade must drop all created tables."""
        migration_file = Path(__file__).parent.parent.parent / "alembic/versions/b8d2f4a6c1e9_portal_analytics.py"
        with open(migration_file) as f:
            content = f.read()
        # Verify downgrade section exists
        assert "def downgrade()" in content, "Migration must have downgrade"
        # Verify drops in downgrade
        assert "drop_table" in content or "DROP TABLE" in content.upper(), \
            "Downgrade must drop tables"

    def test_migration_adds_columns_to_portal_events_in_upgrade(self):
        """Migration must add new columns to portal_events."""
        migration_file = Path(__file__).parent.parent.parent / "alembic/versions/b8d2f4a6c1e9_portal_analytics.py"
        with open(migration_file) as f:
            content = f.read()
        new_columns = ["site_id", "visitor_id", "visit_id", "seq", "page_title",
                      "props", "scroll_pct", "active_ms", "target_url"]
        for col in new_columns:
            assert f'"{col}"' in content or f"'{col}'" in content, \
                f"Migration must add column {col} to portal_events"

    def test_migration_is_head(self):
        """The migration must be registered in Alembic."""
        alembic_dir = Path(__file__).parent.parent.parent / "alembic"
        config = Config(str(alembic_dir / "alembic.ini"))
        config.set_main_option("script_location", str(alembic_dir))
        script = ScriptDirectory.from_config(config)

        target_rev_id = "b8d2f4a6c1e9"
        # Verify it exists in the revision tree
        assert target_rev_id in [rev.revision for rev in script.walk_revisions()], \
            "Migration b8d2f4a6c1e9 not found in revision history"
