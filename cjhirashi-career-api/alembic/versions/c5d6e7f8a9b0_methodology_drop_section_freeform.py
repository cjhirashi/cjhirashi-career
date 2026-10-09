"""operational_methodologies: retirar el texto libre section / subsection / notes

Spec 005 · RF-001 / RF-017 / RF-019. El vínculo con las Secciones del Admin
queda expresado únicamente por `section_ids` (JSONB, feature 004). Los tres
campos de texto libre `section`, `subsection` y `notes` se retiran.

Antes del `DROP` se vuelca `id`, `user_id`, `section`, `subsection`, `notes` de
cada fila a `operational_methodologies_freeform_backup` (RF-017) para poder
revertir. **No** se hace backfill de `section_ids` a partir de `section`
(RF-019): la columna queda intacta.

`upgrade()` es idempotente (RF-001): toda la DDL va guardada con
`IF [NOT] EXISTS`, un segundo `upgrade` no falla.

Revision ID: c5d6e7f8a9b0
Revises: b3d4e5f6a7c8
"""
from typing import Sequence, Union

from alembic import op

revision: str = "c5d6e7f8a9b0"
down_revision: Union[str, None] = "b3d4e5f6a7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FREEFORM_COLUMNS = ("section", "subsection", "notes")


def upgrade() -> None:
    # 1. Respaldo del texto libre ANTES del DROP (RF-017). Idempotente:
    #    CREATE TABLE IF NOT EXISTS + un único INSERT ... SELECT. Re-correr la
    #    migración vuelve a volcar el estado actual (ya sin las columnas -> el
    #    INSERT no aporta filas nuevas porque las columnas no existen; ver nota).
    op.execute(
        "CREATE TABLE IF NOT EXISTS operational_methodologies_freeform_backup ("
        "id text, "
        "user_id text, "
        "section text, "
        "subsection text, "
        "notes text, "
        "backed_up_at timestamptz NOT NULL DEFAULT now())"
    )
    # El INSERT sólo tiene sentido mientras las columnas existan; si ya se
    # retiraron (segundo upgrade), se omite para no romper.
    op.execute(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'operational_methodologies' AND column_name = 'section') "
        "THEN "
        "INSERT INTO operational_methodologies_freeform_backup "
        "(id, user_id, section, subsection, notes) "
        "SELECT id, user_id, section, subsection, notes FROM operational_methodologies; "
        "END IF; "
        "END $$"
    )

    # 2. Índice de `section` (autogenerado por SQLAlchemy: index=True) — RF-001.
    op.execute("DROP INDEX IF EXISTS ix_operational_methodologies_section")

    # 3. DROP de las 3 columnas de texto libre — idempotente (RF-001).
    #    section_ids (JSONB) NO se toca (RF-019).
    for col in _FREEFORM_COLUMNS:
        op.execute(
            f"ALTER TABLE operational_methodologies DROP COLUMN IF EXISTS {col}"
        )


def downgrade() -> None:
    # Re-crea las 3 columnas (nullable) y restaura SÓLO las filas que quedaron
    # respaldadas en operational_methodologies_freeform_backup por `upgrade()`.
    # Filas creadas después del upgrade no tienen respaldo -> quedan con NULL.
    op.execute(
        "ALTER TABLE operational_methodologies ADD COLUMN IF NOT EXISTS section varchar(150)"
    )
    op.execute(
        "ALTER TABLE operational_methodologies ADD COLUMN IF NOT EXISTS subsection varchar(150)"
    )
    op.execute(
        "ALTER TABLE operational_methodologies ADD COLUMN IF NOT EXISTS notes text"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_operational_methodologies_section "
               "ON operational_methodologies (section)")
    op.execute(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_name = 'operational_methodologies_freeform_backup') "
        "THEN "
        "UPDATE operational_methodologies m "
        "SET section = b.section, subsection = b.subsection, notes = b.notes "
        "FROM operational_methodologies_freeform_backup b "
        "WHERE b.id = m.id; "
        "END IF; "
        "END $$"
    )
