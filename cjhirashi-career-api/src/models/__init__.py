"""
cjhirashi-career ORM Models
SQLAlchemy models for all database entities.
"""
# Core Models
from models.user import User

# ----------------------------------------------------------------------------
# Career Domain (v2) - 31 tables
# ----------------------------------------------------------------------------

# Dominio 1: Identidad Profesional
from models.personal_profile import PersonalProfile
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
from models.publication import Publication
from models.linkedin_profile import LinkedInProfile
from models.github_profile import GitHubProfile
from models.portal_home import PortalHome
from models.portal_about import PortalAbout
from models.portal_contact import PortalContact

# Dominio 4: Soporte
from models.tag import Tag

# Dominio 5: Metodologías Operativas
from models.operational_methodology import OperationalMethodology

# Agent System (Motor de Agentes)
from models.agent_system_usage_logs import AgentSystemUsageLog
from models.agent_system_usage_round_logs import AgentSystemUsageRoundLog
from models.agent_system_settings import AgentSystemSettings
from models.agent_system_profile_prompts import AgentSystemProfilePrompt
from models.agent_system_profile_photos import AgentSystemProfilePhoto
from models.agent_system_delegation import AgentSystemDelegation
from models.admin_section_group import AdminSectionGroup
from models.admin_section_l1 import AdminSectionL1
from models.admin_section_l2 import AdminSectionL2
from models.admin_section_l3 import AdminSectionL3
from models.admin_view import AdminView
from models.agent_system_custom_tools import AgentSystemCustomTool
from models.agent_system_conversations import AgentSystemConversation, AgentSystemConversationMessage
from models.agent_system_tasks import AgentSystemTask
from models.user_notification import UserNotification
from models.error_report import ErrorReport
from models.pdf_output_template import PdfOutputTemplate
from models.pdf_template_style import PdfTemplateStyle

# ----------------------------------------------------------------------------
# LinkedIn Integration
# ----------------------------------------------------------------------------

from models.linkedin_connection import LinkedInConnection
from models.linkedin_post import LinkedInPost

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
    "PersonalProfile",
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
    "Publication",
    "LinkedInProfile",
    "GitHubProfile",
    "PortalHome",
    "PortalAbout",
    "PortalContact",
    # Support domain
    "Tag",
    # Operational methodologies domain
    "OperationalMethodology",
    # Agent System (Motor de Agentes)
    "AgentSystemUsageLog",
    "AgentSystemUsageRoundLog",
    "AgentSystemSettings",
    "AgentSystemProfilePrompt",
    "AgentSystemProfilePhoto",
    "AgentSystemDelegation",
    "AdminSectionGroup",
    "AdminSectionL1",
    "AdminSectionL2",
    "AdminSectionL3",
    "AdminView",
    "AgentSystemCustomTool",
    "AgentSystemConversation",
    "AgentSystemConversationMessage",
    "AgentSystemTask",
    "UserNotification",
    "ErrorReport",
    "PdfOutputTemplate",
    "PdfTemplateStyle",
    # LinkedIn integration
    "LinkedInConnection",
    "LinkedInPost",
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
