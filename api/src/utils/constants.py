"""
Constantes globales de la aplicación.
"""

# ============================================================================
# COMPETENCY CONSTANTS
# ============================================================================
COMPETENCY_TYPES = ["técnica", "transferible", "negocio"]
COMPETENCY_LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]

# ============================================================================
# EMPLOYMENT CONSTANTS
# ============================================================================
EMPLOYMENT_TYPES = ["full-time", "part-time", "contract", "freelance", "internship"]

# ============================================================================
# INTERVIEW CONSTANTS
# ============================================================================
INTERVIEW_TYPES = ["phone", "video", "technical", "behavioral", "coding", "system_design"]
INTERVIEW_ROUNDS = ["screening", "round_1", "round_2", "round_3", "final", "offer"]

# ============================================================================
# NETWORKING CONSTANTS
# ============================================================================
RELATIONSHIP_TYPES = ["mentor", "peer", "mentee", "colleague", "friend", "professional_contact"]
CONTACT_STATUSES = ["active", "inactive", "blocked"]

# ============================================================================
# JOB STRATEGY CONSTANTS
# ============================================================================
JOB_STRATEGY_STATUSES = ["active", "passive", "completed", "paused", "on_hold"]
REMOTE_PREFERENCES = ["remote", "onsite", "hybrid", "flexible"]

# ============================================================================
# VACANCY CONSTANTS
# ============================================================================
VACANCY_STATUSES = ["saved", "applied", "rejected", "pending", "accepted", "archived"]

# ============================================================================
# ERROR CONSTANTS
# ============================================================================
ERROR_USER_NOT_FOUND = "USER_NOT_FOUND"
ERROR_INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
ERROR_DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
ERROR_UNAUTHORIZED = "UNAUTHORIZED"
ERROR_VALIDATION_ERROR = "VALIDATION_ERROR"
ERROR_INTERNAL_SERVER = "INTERNAL_SERVER_ERROR"

ERROR_MESSAGES = {
    ERROR_USER_NOT_FOUND: "Usuario no encontrado",
    ERROR_INVALID_CREDENTIALS: "Credenciales inválidas",
    ERROR_DOCUMENT_NOT_FOUND: "Documento no encontrado",
    ERROR_UNAUTHORIZED: "No autorizado",
    ERROR_VALIDATION_ERROR: "Error de validación",
    ERROR_INTERNAL_SERVER: "Error interno del servidor"
}
