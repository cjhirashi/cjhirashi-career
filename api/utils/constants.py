"""
Constantes globales de la aplicación.
"""

# Tipos de documentos permitidos
DOCUMENT_TYPES = ["cv", "cover_letter", "invoice", "report"]

# Códigos de error
ERROR_USER_NOT_FOUND = "USER_NOT_FOUND"
ERROR_INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
ERROR_DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
ERROR_UNAUTHORIZED = "UNAUTHORIZED"
ERROR_VALIDATION_ERROR = "VALIDATION_ERROR"
ERROR_INTERNAL_SERVER = "INTERNAL_SERVER_ERROR"

# Mensajes de error
ERROR_MESSAGES = {
    ERROR_USER_NOT_FOUND: "Usuario no encontrado",
    ERROR_INVALID_CREDENTIALS: "Credenciales inválidas",
    ERROR_DOCUMENT_NOT_FOUND: "Documento no encontrado",
    ERROR_UNAUTHORIZED: "No autorizado",
    ERROR_VALIDATION_ERROR: "Error de validación",
    ERROR_INTERNAL_SERVER: "Error interno del servidor"
}
