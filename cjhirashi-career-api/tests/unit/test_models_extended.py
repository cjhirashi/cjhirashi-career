"""
Extended model tests para mejorar cobertura.
Tests para Identity, Competency, Evidence, JobStrategy, Vacancy, etc.
"""
import pytest
from datetime import date, datetime
from sqlalchemy import select
from models import (
    Identity, Competency, Vacancy,
    NetworkingContact, Interview, RefreshToken, FileUpload,
    Metrics, Event, AuditLog, UserSession
)


class TestIdentityModel:
    """Tests para Identity model."""

    @pytest.mark.asyncio
    async def test_identity_full_creation(self, db_session, test_user):
        """Crear una identidad completa con todos los campos."""
        identity = Identity(
            user_id=test_user.id,
            passion="Crear impacto con tecnología",
            profession="Arquitecto de software",
            vocation="Mentorizar a otros desarrolladores",
            mission="Revolucionar la industria tech",
            key_strengths="Experiencia en patrones SOLID",
            unique_value_prop="Soluciones escalables y mantenibles"
        )
        db_session.add(identity)
        await db_session.flush()
        await db_session.refresh(identity)

        assert identity.id is not None
        assert identity.mission == "Revolucionar la industria tech"
        assert identity.user_id == test_user.id


class TestCompetencyExtended:
    """Extended tests para Competency model."""

    @pytest.mark.asyncio
    async def test_competency_with_all_fields(self, db_session, test_user):
        """Crear competencia con todos los campos."""
        from models.competencies import CompetencyType, CompetencyLevel
        comp = Competency(
            user_id=test_user.id,
            name="FastAPI",
            description="Backend framework development",
            competency_type=CompetencyType.TECHNICAL,
            proficiency_level=CompetencyLevel.EXPERT,
            proficiency_score=95,
            years_of_experience=4,
            endorsement_count=25,
            is_featured=True
        )
        db_session.add(comp)
        await db_session.flush()
        await db_session.refresh(comp)

        assert comp.proficiency_score == 95
        assert comp.endorsement_count == 25
        assert comp.is_featured is True

    @pytest.mark.asyncio
    async def test_competency_types(self, db_session, test_user):
        """Verificar que se pueden crear competencias de diferentes tipos."""
        from models.competencies import CompetencyType
        types = [CompetencyType.TECHNICAL, CompetencyType.TRANSFERABLE, CompetencyType.BUSINESS]

        for comp_type in types:
            comp = Competency(
                user_id=test_user.id,
                name=f"Skill_{comp_type.value}",
                competency_type=comp_type
            )
            db_session.add(comp)

        await db_session.flush()

        result = await db_session.execute(
            select(Competency).where(Competency.user_id == test_user.id)
        )
        competencies = result.scalars().all()
        assert len(competencies) == 3


class TestVacancyModel:
    """Tests para Vacancy model."""

    @pytest.mark.asyncio
    async def test_vacancy_creation(self, db_session, test_user):
        """Crear una oferta de empleo."""
        vacancy = Vacancy(
            user_id=test_user.id,
            title="Software Engineer",
            company="Google",
            url="https://careers.google.com/job123",
            description="Build scalable systems",
            salary_range="$150k-$180k",
            location="San Francisco, CA",
            employment_type="full-time",
            status="saved"
        )
        db_session.add(vacancy)
        await db_session.flush()
        await db_session.refresh(vacancy)

        assert vacancy.company == "Google"
        assert vacancy.status == "saved"

    @pytest.mark.asyncio
    async def test_vacancy_status_values(self, db_session, test_user):
        """Verificar status values para vacancy."""
        for status in ["saved", "applied", "rejected", "accepted"]:
            vacancy = Vacancy(
                user_id=test_user.id,
                title=f"Job_{status}",
                status=status
            )
            db_session.add(vacancy)

        await db_session.flush()


class TestNetworkingContactModel:
    """Tests para NetworkingContact model."""

    @pytest.mark.asyncio
    async def test_networking_contact_creation(self, db_session, test_user):
        """Crear un contacto de networking."""
        from datetime import datetime, timezone

        contact = NetworkingContact(
            user_id=test_user.id,
            name="John Doe",
            title="CTO",
            company="Tech Corp",
            email="john@techcorp.com",
            phone="+1 (555) 123-4567",
            linkedin_url="https://linkedin.com/in/johndoe",
            relationship_type="mentor",
            contact_status="active",
            last_contact_date=datetime.now(timezone.utc),
            notes="Great mentor in architecture"
        )
        db_session.add(contact)
        await db_session.flush()
        await db_session.refresh(contact)

        assert contact.name == "John Doe"
        assert contact.relationship_type == "mentor"


class TestInterviewModel:
    """Tests para Interview model."""

    @pytest.mark.asyncio
    async def test_interview_creation(self, db_session, test_user):
        """Crear un registro de entrevista."""
        from datetime import datetime, timezone

        interview = Interview(
            user_id=test_user.id,
            company="Google",
            position="Software Engineer",
            interview_type="technical",
            interview_round="round_1",
            scheduled_at=datetime.now(timezone.utc),
            interviewer_name="Jane Smith",
            interviewer_email="jane@google.com",
            interview_format="video",
            duration_minutes=60,
            feedback="Excellent coding skills",
            feedback_rating=9,
            status="completed"
        )
        db_session.add(interview)
        await db_session.flush()
        await db_session.refresh(interview)

        assert interview.company == "Google"
        assert interview.feedback_rating == 9


class TestRefreshTokenModel:
    """Tests para RefreshToken model."""

    @pytest.mark.asyncio
    async def test_refresh_token_creation(self, db_session, test_user):
        """Crear un refresh token."""
        from datetime import datetime, timezone, timedelta

        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        token = RefreshToken(
            user_id=test_user.id,
            token="token_value_example",
            expires_at=expires_at,
            is_revoked=False
        )
        db_session.add(token)
        await db_session.flush()
        await db_session.refresh(token)

        assert token.user_id == test_user.id
        assert token.is_revoked is False


class TestFileUploadModel:
    """Tests para FileUpload model."""

    @pytest.mark.asyncio
    async def test_file_upload_creation(self, db_session, test_user):
        """Crear un registro de archivo subido."""
        file = FileUpload(
            user_id=test_user.id,
            filename="resume.pdf",
            file_type="pdf",
            file_size=102400,
            file_path="/uploads/resume_123.pdf",
            s3_url="https://s3.amazonaws.com/resume_123.pdf",
            is_public=False
        )
        db_session.add(file)
        await db_session.flush()
        await db_session.refresh(file)

        assert file.filename == "resume.pdf"
        assert file.file_size == 102400


class TestMetricsModel:
    """Tests para Metrics model."""

    @pytest.mark.asyncio
    async def test_metrics_creation(self, db_session, test_user):
        """Crear un registro de métrica."""
        metric = Metrics(
            user_id=test_user.id,
            metric_type="applications_sent",
            value=25.0,
            period="weekly"
        )
        db_session.add(metric)
        await db_session.flush()
        await db_session.refresh(metric)

        assert metric.metric_type == "applications_sent"
        assert metric.value == 25.0


class TestEventModel:
    """Tests para Event model."""

    @pytest.mark.asyncio
    async def test_event_creation(self, db_session, test_user):
        """Crear un registro de evento."""
        event = Event(
            user_id=test_user.id,
            event_type="login",
            event_data='{"location": "San Francisco", "device": "Chrome"}',
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0..."
        )
        db_session.add(event)
        await db_session.flush()
        await db_session.refresh(event)

        assert event.event_type == "login"
        assert event.user_id == test_user.id


class TestAuditLogModel:
    """Tests para AuditLog model."""

    @pytest.mark.asyncio
    async def test_audit_log_creation(self, db_session, test_user):
        """Crear un registro de auditoría."""
        log = AuditLog(
            user_id=test_user.id,
            action="create_competency",
            entity_type="Competency",
            entity_id=123,
            changes='{"name": "Python"}',
            ip_address="192.168.1.1"
        )
        db_session.add(log)
        await db_session.flush()
        await db_session.refresh(log)

        assert log.action == "create_competency"
        assert log.entity_type == "Competency"


class TestUserSessionModel:
    """Tests para UserSession model."""

    @pytest.mark.asyncio
    async def test_user_session_creation(self, db_session, test_user):
        """Crear un registro de sesión."""
        session = UserSession(
            user_id=test_user.id,
            session_token="session_token_123",
            session_hash="hash_123",
            device_type="desktop",
            device_os="MacOS",
            browser_name="Chrome",
            browser_version="120.0",
            ip_address="192.168.1.1",
            country="United States",
            city="San Francisco",
            is_active=True,
            page_views=10,
            api_calls=25
        )
        db_session.add(session)
        await db_session.flush()
        await db_session.refresh(session)

        assert session.device_type == "desktop"
        assert session.page_views == 10
        assert session.is_active is True
