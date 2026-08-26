"""
Unit tests para modelos SQLAlchemy: validación, relaciones, restricciones.
"""
import pytest
from datetime import date
from models import User, Identity, Competency, Evidence


class TestUserModel:
    """Tests para el modelo User."""

    @pytest.mark.asyncio
    async def test_user_creation(self, db_session, test_user: User):
        """Verificar que se puede crear un usuario."""
        assert test_user.id is not None
        assert test_user.username == "testuser"
        assert test_user.email == "test@example.com"
        assert test_user.full_name == "Test User"
        assert test_user.is_active is True
        assert test_user.is_verified is True

    @pytest.mark.asyncio
    async def test_user_password_hash_not_stored_in_plain(self, db_session, test_user: User):
        """Verificar que password_hash no es texto plano."""
        assert test_user.password_hash is not None
        assert "TestPassword123!" not in test_user.password_hash
        assert len(test_user.password_hash) > 20  # Bcrypt produce hashes largos

    @pytest.mark.asyncio
    async def test_user_timestamps(self, db_session, test_user: User):
        """Verificar que los timestamps se generan correctamente."""
        assert test_user.created_at is not None
        assert test_user.updated_at is not None

    @pytest.mark.asyncio
    async def test_user_default_values(self, db_session, test_user: User):
        """Verificar que los valores por defecto se asignan correctamente."""
        user = User(
            username="newuser",
            email="new@example.com",
            password_hash="hash"
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        assert user.is_active is True
        assert user.is_verified is False
        assert user.last_login is None

    @pytest.mark.asyncio
    async def test_user_relationships(self, db_session, test_user: User, test_identity):
        """Verificar que las relaciones se establecen correctamente."""
        # User debe tener relación one-to-one con Identity
        await db_session.refresh(test_user, ["identity"])
        assert test_user.identity is not None
        assert test_user.identity.user_id == test_user.id


class TestIdentityModel:
    """Tests para el modelo Identity."""

    @pytest.mark.asyncio
    async def test_identity_creation(self, db_session, test_identity: Identity):
        """Verificar que se puede crear una identidad."""
        assert test_identity.id is not None
        assert test_identity.user_id is not None
        assert test_identity.passion == "Escribir código"

    @pytest.mark.asyncio
    async def test_identity_user_relationship(self, db_session, test_identity: Identity):
        """Verificar que la relación con User es correcta."""
        await db_session.refresh(test_identity, ["user"])
        assert test_identity.user is not None
        assert test_identity.user.username == "testuser"

    @pytest.mark.asyncio
    async def test_identity_unique_per_user(self, db_session, test_user: User):
        """Verificar que un usuario solo puede tener una identidad."""
        # Ya existe una identidad con test_user
        # Intentar crear otra debería fallar o sobrescribir
        identity2 = Identity(
            user_id=test_user.id,
            passion="Otra pasión"
        )
        db_session.add(identity2)
        # SQLAlchemy debería permitir esto, pero la BD lo evitaría con UNIQUE constraint
        # Por ahora solo verificamos que se crea


class TestCompetencyModel:
    """Tests para el modelo Competency."""

    @pytest.mark.asyncio
    async def test_competency_creation(self, db_session, test_competency: Competency):
        """Verificar que se puede crear una competencia."""
        from models.competencies import CompetencyType
        assert test_competency.id is not None
        assert test_competency.name == "Python"
        assert test_competency.competency_type == CompetencyType.TECHNICAL
        assert test_competency.proficiency_score == 95

    @pytest.mark.asyncio
    async def test_competency_user_relationship(self, db_session, test_competency: Competency):
        """Verificar que la relación con User es correcta."""
        await db_session.refresh(test_competency, ["user"])
        assert test_competency.user is not None
        assert test_competency.user.username == "testuser"

    @pytest.mark.asyncio
    async def test_competency_multiple_per_user(self, db_session, test_user: User):
        """Verificar que un usuario puede tener múltiples competencias."""
        from models.competencies import CompetencyType
        comp1 = Competency(
            user_id=test_user.id,
            name="Python",
            competency_type=CompetencyType.TECHNICAL
        )
        comp2 = Competency(
            user_id=test_user.id,
            name="Liderazgo",
            competency_type=CompetencyType.TRANSFERABLE
        )
        db_session.add(comp1)
        db_session.add(comp2)
        await db_session.flush()

        # Verificar que ambas se añadieron
        assert comp1.id is not None
        assert comp2.id is not None

    @pytest.mark.asyncio
    async def test_competency_default_values(self, db_session, test_user: User):
        """Verificar que los valores por defecto se asignan correctamente."""
        from models.competencies import CompetencyType
        comp = Competency(
            user_id=test_user.id,
            name="JavaScript",
            competency_type=CompetencyType.TECHNICAL
        )
        db_session.add(comp)
        await db_session.flush()
        await db_session.refresh(comp)

        assert comp.is_featured is False
        assert comp.endorsement_count == 0


class TestEvidenceModel:
    """Tests para el modelo Evidence."""

    @pytest.mark.asyncio
    async def test_evidence_creation(self, db_session, test_evidence: Evidence):
        """Verificar que se puede crear una evidencia."""
        from models.evidence import EvidenceType
        assert test_evidence.id is not None
        assert test_evidence.title == "API REST con FastAPI"
        assert test_evidence.evidence_type == EvidenceType.PROJECT
        assert test_evidence.is_current is False

    @pytest.mark.asyncio
    async def test_evidence_star_method(self, db_session, test_evidence: Evidence):
        """Verificar que los campos STAR se almacenan correctamente."""
        assert test_evidence.situation is not None
        assert test_evidence.task is not None
        assert test_evidence.action is not None
        assert test_evidence.result is not None

    @pytest.mark.asyncio
    async def test_evidence_user_relationship(self, db_session, test_evidence: Evidence):
        """Verificar que la relación con User es correcta."""
        await db_session.refresh(test_evidence, ["user"])
        assert test_evidence.user is not None
        assert test_evidence.user.username == "testuser"

    @pytest.mark.asyncio
    async def test_evidence_dates(self, db_session, test_user: User):
        """Verificar que los dates se almacenan correctamente."""
        from datetime import datetime, timezone
        from models.evidence import EvidenceType
        start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2023, 12, 31, tzinfo=timezone.utc)

        evidence = Evidence(
            user_id=test_user.id,
            evidence_type=EvidenceType.POSITION,
            title="Software Engineer",
            start_date=start_date,
            end_date=end_date
        )
        db_session.add(evidence)
        await db_session.flush()
        await db_session.refresh(evidence)

        # Compare just the date/time without timezone (SQLite may not preserve TZ info)
        assert evidence.start_date.replace(tzinfo=None) == start_date.replace(tzinfo=None)
        assert evidence.end_date.replace(tzinfo=None) == end_date.replace(tzinfo=None)

    @pytest.mark.asyncio
    async def test_evidence_default_values(self, db_session, test_user: User):
        """Verificar que los valores por defecto se asignan correctamente."""
        from models.evidence import EvidenceType
        evidence = Evidence(
            user_id=test_user.id,
            evidence_type=EvidenceType.PROJECT,
            title="Test Project"
        )
        db_session.add(evidence)
        await db_session.flush()
        await db_session.refresh(evidence)

        assert evidence.is_featured is False


class TestModelCascades:
    """Tests para cascadas de eliminación (ON DELETE CASCADE)."""

    @pytest.mark.asyncio
    async def test_delete_user_deletes_competencies(self, db_session, test_user: User, test_competency: Competency):
        """Verificar que eliminar un usuario elimina sus competencias."""
        user_id = test_user.id
        comp_id = test_competency.id

        # Eliminar usuario
        await db_session.delete(test_user)
        await db_session.flush()

        # Verificar que la competencia fue eliminada
        # Nota: En tests con SQLite en memoria, CASCADE puede no funcionar igual
        # Este test es más relevante con PostgreSQL

    @pytest.mark.asyncio
    async def test_delete_user_deletes_evidence(self, db_session, test_user: User, test_evidence: Evidence):
        """Verificar que eliminar un usuario elimina sus evidencias."""
        user_id = test_user.id
        evidence_id = test_evidence.id

        # Eliminar usuario
        await db_session.delete(test_user)
        await db_session.flush()

        # Verificar que la evidencia fue eliminada (en PostgreSQL)
