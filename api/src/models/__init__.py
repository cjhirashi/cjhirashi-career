"""
Portafolio-cjhirashi ORM Models
SQLAlchemy models for all database entities.
"""
# Core Models
from models.user import User

# ----------------------------------------------------------------------------
# Career Domain (v2) - 30 tables
# ----------------------------------------------------------------------------

# Dominio 1: Identidad Profesional
from models.differentiator import Differentiator
from models.identity import Identity
from models.identity_reflection import IdentityReflection
from models.competencies import Competency
from models.certification import Certification
from models.target_role import TargetRole
from models.work_history import WorkHistory
from models.achievement import Achievement
from models.star_story import StarStory
from models.career_review import CareerReview
from models.role_gap_analysis import RoleGapAnalysis
from models.project import Project

# Dominio 2: Operativa de Búsqueda
from models.fit_scoring_factor import FitScoringFactor
from models.market_segment import MarketSegment
from models.role_narrative import RoleNarrative
from models.search_plan import SearchPlan
from models.networking_contact import NetworkingContact
from models.target_company import TargetCompany
from models.vacancy import Vacancy
from models.cv_version import CVVersion
from models.cover_letter_version import CoverLetterVersion
from models.application import Application
from models.application_interaction import ApplicationInteraction
from models.interview import Interview
from models.contact_interaction import ContactInteraction
from models.networking_activity import NetworkingActivity

# Dominio 3: Presencia Digital
from models.digital_platform import DigitalPlatform
from models.content_piece import ContentPiece
from models.publication import Publication

# Dominio 4: Soporte
from models.tag import Tag

# ----------------------------------------------------------------------------
# Base System (v1) - unchanged
# ----------------------------------------------------------------------------

# Security & Authentication
from models.refresh_token import RefreshToken

# File Management
from models.file_upload import FileUpload, FileType

# Analytics & Tracking
from models.event import Event, EventType
from models.audit_log import AuditLog, AuditAction
from models.metrics import Metrics
from models.user_session import UserSession

__all__ = [
    # Core
    "User",
    # Identity domain
    "Differentiator",
    "Identity",
    "IdentityReflection",
    "Competency",
    "Certification",
    "TargetRole",
    "WorkHistory",
    "Achievement",
    "StarStory",
    "CareerReview",
    "RoleGapAnalysis",
    "Project",
    # Search domain
    "FitScoringFactor",
    "MarketSegment",
    "RoleNarrative",
    "SearchPlan",
    "NetworkingContact",
    "TargetCompany",
    "Vacancy",
    "CVVersion",
    "CoverLetterVersion",
    "Application",
    "ApplicationInteraction",
    "Interview",
    "ContactInteraction",
    "NetworkingActivity",
    # Digital presence domain
    "DigitalPlatform",
    "ContentPiece",
    "Publication",
    # Support domain
    "Tag",
    # Security
    "RefreshToken",
    # Files
    "FileUpload",
    "FileType",
    # Analytics
    "Event",
    "EventType",
    "AuditLog",
    "AuditAction",
    "Metrics",
    "UserSession",
]
