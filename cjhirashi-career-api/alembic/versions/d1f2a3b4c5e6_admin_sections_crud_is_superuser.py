"""admin_sections_crud_is_superuser

ADR-023 (corrección, 2026-08-29): CRUD completo de grupos/secciones desde el Admin +
campo visibility_level en las 4 tablas de jerarquía + admin_views + is_superuser en users.
Migra s1-17 ('settings-sections') al grupo protegido 'admin' y lo renombra a 'admin-sections'.

Revision ID: d1f2a3b4c5e6
Revises: c4d5e6f7a8b9
Create Date: 2026-08-29
"""
from alembic import op
import sqlalchemy as sa

revision = "d1f2a3b4c5e6"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. visibility_level en las 4 tablas de jerarquía + admin_views
    for table in (
        "admin_section_groups",
        "admin_sections_l1",
        "admin_sections_l2",
        "admin_sections_l3",
        "admin_views",
    ):
        op.add_column(
            table,
            sa.Column(
                "visibility_level",
                sa.String(50),
                nullable=False,
                server_default="standard",
            ),
        )

    # 2. is_superuser en users (backfill: todos los usuarios existentes son superusuario)
    op.add_column(
        "users",
        sa.Column(
            "is_superuser",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.execute("UPDATE users SET is_superuser = true")

    # 3. Grupo protegido 'admin' (grp-12, siguiente libre tras grp-1..grp-11)
    conn = op.get_bind()

    existing_group = conn.execute(
        sa.text("SELECT id FROM admin_section_groups WHERE system_name = 'admin'")
    ).scalar_one_or_none()

    if existing_group is None:
        conn.execute(
            sa.text(
                "INSERT INTO admin_section_groups "
                "(id, system_name, name, sort_order, origin, visibility_level, created_at, updated_at) "
                "VALUES ('grp-12', 'admin', 'Administración', 0, 'code', 'superuser', now(), now())"
            )
        )
        existing_group = "grp-12"

    # Bump la secuencia para que el próximo INSERT por API no colisione con grp-12
    conn.execute(sa.text("SELECT setval('grp_id_seq', 12, true)"))

    # 4. Migrar s1-17 ('settings-sections') al grupo admin y renombrar a 'admin-sections'.
    #    Si ya existe una fila con system_name='admin-sections', no hacer nada.
    #    Si existe la fila con path='/settings/sections' (legacy), actualizarla.
    #    Si ninguna existe, crear s1-55 (siguiente libre tras s1-1..s1-54).
    existing_admin_section = conn.execute(
        sa.text("SELECT id FROM admin_sections_l1 WHERE system_name = 'admin-sections'")
    ).scalar_one_or_none()

    if existing_admin_section is None:
        legacy_section = conn.execute(
            sa.text("SELECT id FROM admin_sections_l1 WHERE path = '/settings/sections'")
        ).scalar_one_or_none()

        if legacy_section is not None:
            # Migrar s1-17 al grupo admin, renombrar system_name, marcar superuser
            conn.execute(
                sa.text(
                    "UPDATE admin_sections_l1 "
                    "SET group_id = :gid, system_name = 'admin-sections', "
                    "    visibility_level = 'superuser', updated_at = now() "
                    "WHERE id = :sid"
                ),
                {"gid": existing_group, "sid": legacy_section},
            )
        else:
            # BD fresca sin legacy: insertar nueva sección
            conn.execute(
                sa.text(
                    "INSERT INTO admin_sections_l1 "
                    "(id, group_id, system_name, label, path, section_type, sort_order, "
                    " origin, visibility_level, created_at, updated_at) "
                    "VALUES ('s1-55', :gid, 'admin-sections', 'Secciones del Admin', "
                    "        '/settings/sections', 'functional', 0, 'code', 'superuser', now(), now())"
                ),
                {"gid": existing_group},
            )
            conn.execute(sa.text("SELECT setval('s1_id_seq', 55, true)"))


def downgrade() -> None:
    # Revertir la migración de la sección admin-sections (renombrar de vuelta o eliminar)
    conn = op.get_bind()

    # Si la sección fue migrada desde legacy (s1-17), revertir al grupo Settings y nombre original
    settings_group = conn.execute(
        sa.text("SELECT id FROM admin_section_groups WHERE system_name = 'settings'")
    ).scalar_one_or_none()

    if settings_group is not None:
        conn.execute(
            sa.text(
                "UPDATE admin_sections_l1 "
                "SET group_id = :gid, system_name = 'settings-sections', "
                "    visibility_level = 'standard', updated_at = now() "
                "WHERE system_name = 'admin-sections' AND path = '/settings/sections'"
            ),
            {"gid": settings_group},
        )
    else:
        # Si no hay grupo Settings (BD fresca con s1-55), eliminar
        conn.execute(
            sa.text("DELETE FROM admin_sections_l1 WHERE system_name = 'admin-sections'")
        )

    # Eliminar el grupo admin
    conn.execute(
        sa.text("DELETE FROM admin_section_groups WHERE system_name = 'admin'")
    )

    # Quitar is_superuser de users
    op.drop_column("users", "is_superuser")

    # Quitar visibility_level de todas las tablas
    for table in (
        "admin_views",
        "admin_sections_l3",
        "admin_sections_l2",
        "admin_sections_l1",
        "admin_section_groups",
    ):
        op.drop_column(table, "visibility_level")
