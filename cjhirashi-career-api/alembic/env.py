"""
Alembic environment - runs migrations with a *sync* engine (psycopg2), even
though the app itself talks to PostgreSQL via asyncpg (see database.py).
Alembic's autogenerate/offline machinery assumes a sync DBAPI; converting
the driver here (asyncpg -> psycopg2) is simpler than wiring async support
for what is, in practice, an occasional one-off admin operation.

First real migration: 2026-08-21 (see versions/). Before that, the schema
was created entirely from ../init.sql and Alembic tracked nothing - see
docs/DATABASE.md, "Estado de las Tablas".
"""
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make `from config import settings` / `from database import Base` (and every
# `models.*` module they pull in) resolvable, exactly like tests/conftest.py
# does - the app's own code imports things as `models.xxx`, not `src.models.xxx`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import settings  # noqa: E402
from database import Base  # noqa: E402
import models  # noqa: E402,F401  (registers every ORM model on Base.metadata)

# this is the Alembic Config object, which provides access to the values
# within the .ini file in use.
config = context.config

# Interpret the config file for Python logging - this line sets up loggers.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# `database.py` uses `postgresql+asyncpg://...`; Alembic's default sync
# machinery needs a sync driver, hence the swap to psycopg2 (already a
# dependency - see requirements.txt).
sync_database_url = settings.DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
)
config.set_main_option("sqlalchemy.url", sync_database_url)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an
    Engine is acceptable here as well. By skipping the Engine creation we
    don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
