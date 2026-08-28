"""Registro en código de las secciones del Admin Panel.

Una sección es una pantalla (o grupo de vistas) que un agente puede dominar:
tabla CRUD, área funcional (p. ej. API LinkedIn), métricas o bucket de archivos.
Los overrides editables viven en PostgreSQL (`admin_section_overrides`).

Identificadores (ADR-021):
- ``id`` es el PK sintético ``sec-<n>`` (prefijo ``sec-``, análogo a ``err-N``).
  Es la clave canónica en TODO: ``admin_section_overrides.section_id``, propiedad
  de secciones por agente, tool Bedrock ``admin_section_settings`` y la URL del
  Admin ``/settings/sections/:id``.
- ``system_name`` es el slug legible (``dashboard``, ``career-projects``…), antes
  llamado "Id". Sirve para migración/depuración y para mostrarlo en la UI.

REGLA DE NUMERACIÓN (CONGELADA): cada ``sec-<n>`` se asigna explícitamente en
código, una vez y para siempre. No se reutiliza ni se reordena. Sección nueva →
siguiente entero libre (55, 56…). Sección eliminada → su número queda retirado
(hueco permanente). El orden actual es: ``_SECTIONS`` (sec-1..sec-19) y luego
``_CAREER_ROWS`` (sec-20..sec-54).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from services.bedrock.agent_profiles import (
    AGENT_CHANGELOG,
    AGENT_CONFIGURATION,
    AGENT_DIGITAL_PRESENCE,
    AGENT_GITHUB,
    AGENT_LINKEDIN_PUBLISHING,
    AGENT_METHODOLOGIES,
    AGENT_NETWORKING,
    AGENT_ORCHESTRATOR,
    AGENT_PDF_DESIGN,
    AGENT_PROFESSIONAL_IDENTITY,
    AGENT_SEARCH_OPERATIONS,
    AGENT_SETTINGS,
    AGENT_SUPPORT,
    AGENT_TASK_MANAGER,
    AGENT_VACANCY_SEARCH,
    get_profile,
)

SECTION_TABLE = "table"
SECTION_FUNCTIONAL = "functional"
SECTION_METRICS = "metrics"
SECTION_BUCKET = "bucket"

SECTION_TYPE_LABELS = {
    SECTION_TABLE: "tabla",
    SECTION_FUNCTIONAL: "funcional",
    SECTION_METRICS: "métricas",
    SECTION_BUCKET: "bucket",
}

# L3 no tiene chat: el contextual de esa sección habla con este L1/L2.
_L3_CHAT_FALLBACK = {
    AGENT_LINKEDIN_PUBLISHING: AGENT_DIGITAL_PRESENCE,
    AGENT_VACANCY_SEARCH: AGENT_SEARCH_OPERATIONS,
    AGENT_GITHUB: AGENT_DIGITAL_PRESENCE,
    AGENT_TASK_MANAGER: AGENT_ORCHESTRATOR,
    AGENT_CHANGELOG: AGENT_ORCHESTRATOR,
}


@dataclass(frozen=True)
class AdminViewSpec:
    key: str
    label: str
    description: str
    sidebar_title: str
    sidebar_body: str


@dataclass(frozen=True)
class AdminSectionSpec:
    id: str  # PK sintético ``sec-<n>`` (ADR-021)
    system_name: str  # slug legible: dashboard, career-projects, settings-error-reports…
    label: str
    path: str
    section_type: str
    default_agent_profile_id: Optional[str]
    description: str
    views: Tuple[AdminViewSpec, ...]
    resource_key: Optional[str] = None
    related_tools: Tuple[str, ...] = ()
    group: str = ""
    sort_order: int = 0


def chat_agent_id(agent_profile_id: Optional[str]) -> Optional[str]:
    """Agente user-facing para el chat contextual de una sección."""
    if not agent_profile_id:
        return AGENT_ORCHESTRATOR
    profile = get_profile(agent_profile_id)
    if profile.user_facing:
        return profile.id
    return _L3_CHAT_FALLBACK.get(profile.id, AGENT_ORCHESTRATOR)


def _view(
    key: str,
    label: str,
    description: str,
    sidebar_title: str,
    sidebar_body: str,
) -> AdminViewSpec:
    return AdminViewSpec(key, label, description, sidebar_title, sidebar_body)


def _main_view(title: str, description: str, body: str) -> Tuple[AdminViewSpec, ...]:
    return (_view("main", "Principal", description, title, body),)


def _crud_views(
    label: str,
    description: str,
    singleton: bool,
    *,
    allow_create: bool = True,
) -> Tuple[AdminViewSpec, ...]:
    if singleton:
        body = (
            f"{description} Este es tu único registro. Edítalo con el botón de la "
            "tarjeta cuando cambie la información — no se crean registros adicionales."
        )
        return (_view("main", "Ficha", description, label, body),)
    if allow_create:
        list_body = (
            f"{description} Usa el botón de alta para agregar un registro. Desde la "
            "tabla puedes editar o eliminar cualquiera existente."
        )
        edit_body = (
            f"Edición de un registro de {label}. Los cambios se guardan al confirmar."
        )
    else:
        list_body = (
            f"{description} Abre un registro para verlo o editarlo. Los perfiles se "
            "definen en código: no se pueden crear ni eliminar desde aquí."
        )
        edit_body = (
            f"Edición de overrides de {label}. El perfil en código no se crea ni se borra."
        )
    view_body = (
        f"Vista de un registro de {label}. Revisa los campos; usa Edición para cambiarlos."
    )
    return (
        _view("list", "Lista", f"Tabla de {label}.", label, list_body),
        _view("view", "Vista", f"Detalle de un registro de {label}.", label, view_body),
        _view("edit", "Edición", f"Formulario de edición de {label}.", label, edit_body),
    )


def _career(
    number: int,
    resource_key: str,
    label: str,
    agent_id: str,
    group: str,
    sort_order: int,
    description: str,
    singleton: bool = False,
) -> AdminSectionSpec:
    return AdminSectionSpec(
        id=f"sec-{number}",
        system_name=f"career-{resource_key}",
        label=label,
        path=f"/career/{resource_key}",
        section_type=SECTION_TABLE,
        default_agent_profile_id=agent_id,
        description=description,
        views=_crud_views(label, description, singleton),
        resource_key=resource_key,
        group=group,
        sort_order=sort_order,
    )


_SECTIONS: List[AdminSectionSpec] = [
    AdminSectionSpec(
        id="sec-1",
        system_name="dashboard",
        label="Dashboard",
        path="/dashboard",
        section_type=SECTION_METRICS,
        default_agent_profile_id=AGENT_ORCHESTRATOR,
        description="Resumen de actividad de carrera: conteos y búsqueda semanal.",
        views=_main_view(
            "Dashboard",
            "Resumen general de tu actividad de carrera.",
            "Resumen general de tu actividad de carrera: conteos rápidos y tu actividad "
            "de búsqueda semanal. Los datos se calculan a partir de las secciones de Carrera.",
        ),
        group="Métricas",
        sort_order=10,
    ),
    AdminSectionSpec(
        id="sec-2",
        system_name="metrics",
        label="Métricas",
        path="/metrics",
        section_type=SECTION_METRICS,
        default_agent_profile_id=AGENT_ORCHESTRATOR,
        description="Métricas del portafolio público y del panel.",
        views=_main_view(
            "Métricas",
            "Cifras de referencia del portafolio y del panel.",
            "Vista de métricas del portafolio público y del panel. Se llenan conforme "
            "haya tráfico e interacciones reales.",
        ),
        group="Métricas",
        sort_order=11,
    ),
    AdminSectionSpec(
        id="sec-3",
        system_name="search-metrics",
        label="Métricas de Búsqueda",
        path="/search-metrics",
        section_type=SECTION_METRICS,
        default_agent_profile_id=AGENT_SEARCH_OPERATIONS,
        description="Embudo y gráficos de la Operativa de Búsqueda (solo lectura).",
        views=_main_view(
            "Métricas de Búsqueda",
            "Visualización del pipeline de búsqueda.",
            "Visualización gráfica de la Operativa de Búsqueda: embudo, triage de vacantes, "
            "segmentos, networking y plan activo. Se calcula en vivo desde las tablas del dominio.",
        ),
        group="Métricas",
        sort_order=12,
    ),
    AdminSectionSpec(
        id="sec-4",
        system_name="agent-metrics",
        label="Costo y Uso",
        path="/agent/metrics",
        section_type=SECTION_METRICS,
        default_agent_profile_id=AGENT_ORCHESTRATOR,
        description="Tokens, costo estimado y presupuesto diario de Bedrock.",
        views=_main_view(
            "Costo y Uso",
            "Consumo de inferencia de los agentes.",
            "Uso de tokens y costo estimado del chat. El presupuesto diario se configura aquí.",
        ),
        group="Métricas",
        sort_order=13,
    ),
    AdminSectionSpec(
        id="sec-5",
        system_name="files",
        label="Archivos",
        path="/files",
        section_type=SECTION_BUCKET,
        default_agent_profile_id=AGENT_ORCHESTRATOR,
        description="Bucket MinIO: subida, links públicos y borrado permanente.",
        views=_main_view(
            "Archivos",
            "Almacén de archivos del operador.",
            'Sube cualquier archivo y obtén un link público. "Copiar link" copia la URL; '
            '"Eliminar" borra el archivo del bucket de forma permanente.',
        ),
        group="Almacenamiento",
        sort_order=20,
    ),
    AdminSectionSpec(
        id="sec-6",
        system_name="linkedin-publish",
        label="LinkedIn · Publicar",
        path="/linkedin",
        section_type=SECTION_FUNCTIONAL,
        default_agent_profile_id=AGENT_LINKEDIN_PUBLISHING,
        description="Integración API de LinkedIn: OAuth, publicar y programar posts.",
        views=_main_view(
            "LinkedIn · Publicar",
            "Publicación y programación vía API de LinkedIn.",
            "Conecta LinkedIn (OAuth), redacta o programa posts y revisa el estado de la "
            "conexión. No es la ficha del perfil (eso vive en Perfil de LinkedIn).",
        ),
        related_tools=(
            "get_linkedin_status",
            "list_linkedin_posts",
            "create_linkedin_post",
            "delete_scheduled_linkedin_post",
        ),
        group="Presencia Digital",
        sort_order=30,
    ),
    AdminSectionSpec(
        id="sec-7",
        system_name="job-discovery",
        label="Descubrir vacantes",
        path="/job-discovery",
        section_type=SECTION_FUNCTIONAL,
        default_agent_profile_id=AGENT_VACANCY_SEARCH,
        description="Búsqueda e importación de vacantes (Indeed, boards, URL).",
        views=_main_view(
            "Descubrir vacantes",
            "Discovery e importación de ofertas.",
            "Pide al agente que busque vacantes. Autoriza cuáles guardar; se crean como "
            "pending_review. Pegar una URL de LinkedIn jobs/view también importa.",
        ),
        related_tools=(
            "list_job_providers",
            "run_job_discovery",
            "import_job_url",
            "save_job_listings",
        ),
        group="Operativa de Búsqueda",
        sort_order=31,
    ),
    AdminSectionSpec(
        id="sec-8",
        system_name="pdf-templates",
        label="Plantillas PDF",
        path="/agent/pdf-templates",
        section_type=SECTION_TABLE,
        default_agent_profile_id=AGENT_PDF_DESIGN,
        description="HTML de salida WeasyPrint con variables y estilo asociado.",
        views=_crud_views(
            "Plantillas PDF",
            "HTML de plantillas PDF (resource pdf-output-templates).",
            False,
        ),
        resource_key="pdf-output-templates",
        related_tools=("pdf_template", "pdf_style"),
        group="Diseño PDF",
        sort_order=40,
    ),
    AdminSectionSpec(
        id="sec-9",
        system_name="pdf-styles",
        label="Estilos PDF",
        path="/agent/pdf-template-styles",
        section_type=SECTION_TABLE,
        default_agent_profile_id=AGENT_PDF_DESIGN,
        description="CSS reutilizable y guía de clases para plantillas PDF.",
        views=_crud_views(
            "Estilos PDF",
            "Estilos CSS de plantillas PDF (resource pdf-template-styles).",
            False,
        ),
        resource_key="pdf-template-styles",
        related_tools=("pdf_style", "pdf_template"),
        group="Diseño PDF",
        sort_order=41,
    ),
    AdminSectionSpec(
        id="sec-10",
        system_name="agent-tasks",
        label="Tareas",
        path="/tasks",
        section_type=SECTION_TABLE,
        default_agent_profile_id=AGENT_TASK_MANAGER,
        description=(
            "Tablero de trabajo: tareas del usuario o de un agente. "
            "Las de agente se ejecutan a scheduled_at aunque el Admin esté cerrado."
        ),
        views=(
            _view(
                "list",
                "Lista",
                "Tabla de tareas.",
                "Tareas",
                "Crea tareas para ti o para un agente. Si asignas un agente y una fecha, "
                "el scheduler las ejecuta aunque no estés en sesión. Cambia entre lista, "
                "calendario, kanban y Gantt.",
            ),
            _view(
                "kanban",
                "Kanban",
                "Columnas por estado.",
                "Tareas · Kanban",
                "Arrastra el estado con el selector de cada tarjeta. Failed es una ejecución de agente que no terminó.",
            ),
            _view(
                "calendar",
                "Calendario",
                "Tareas por día según scheduled_at o due_at.",
                "Tareas · Calendario",
                "Las tarjetas caen en el día de inicio (scheduled_at) o, si no hay, en la fecha límite.",
            ),
            _view(
                "gantt",
                "Gantt",
                "Línea de tiempo scheduled_at → due_at.",
                "Tareas · Gantt",
                "La barra va del inicio programado a la fecha límite. Sin due_at, se muestra un punto de un día.",
            ),
            _view(
                "view",
                "Vista",
                "Detalle de una tarea.",
                "Tarea",
                "Ficha de la tarea: asignación, horario, prioridad y el último resultado del agente.",
            ),
            _view(
                "edit",
                "Edición",
                "Formulario de edición de una tarea.",
                "Tarea · Edición",
                "Cambia asignación, horario y prioridad. Si asignas un agente y una fecha, "
                "el scheduler la ejecuta aunque no estés en sesión.",
            ),
        ),
        resource_key="agent-tasks",
        group="Principal",
        sort_order=15,
    ),
    AdminSectionSpec(
        id="sec-11",
        system_name="agent-chat",
        label="Chat General",
        path="/agent/chat",
        section_type=SECTION_FUNCTIONAL,
        default_agent_profile_id=AGENT_ORCHESTRATOR,
        description="Chat con el orquestador L1 (delega a especialistas).",
        views=_main_view(
            "Chat General",
            "Conversación con el orquestador.",
            "Habla con el orquestador. Él no opera tablas: delega a los L2/L3 que correspondan.",
        ),
        group="Agente IA",
        sort_order=51,
    ),
    AdminSectionSpec(
        id="sec-12",
        system_name="agent-memory",
        label="Memoria",
        path="/agent/memory",
        section_type=SECTION_FUNCTIONAL,
        default_agent_profile_id=AGENT_ORCHESTRATOR,
        description="Hechos de largo plazo y eventos de memoria del harness.",
        views=_main_view(
            "Memoria",
            "Memoria semántica y de corto plazo.",
            "Consulta lo que el agente ha aprendido (Qdrant) y los eventos de conversación.",
        ),
        group="Agente IA",
        sort_order=52,
    ),
    AdminSectionSpec(
        id="sec-13",
        system_name="agent-instructions",
        label="Instrucciones",
        path="/agent/instructions",
        section_type=SECTION_FUNCTIONAL,
        default_agent_profile_id=AGENT_ORCHESTRATOR,
        description="Prompt global del harness (el suffix por agente vive en el catálogo).",
        views=_main_view(
            "Instrucciones",
            "Prompt global del sistema.",
            "Prompt global. Los suffix por especialista se editan en Settings → Catálogo de Agentes.",
        ),
        group="Agente IA",
        sort_order=53,
    ),
    AdminSectionSpec(
        id="sec-14",
        system_name="agent-tools",
        label="Herramientas",
        path="/agent/tools",
        section_type=SECTION_FUNCTIONAL,
        default_agent_profile_id=AGENT_ORCHESTRATOR,
        description="Servidores MCP registrados para el harness.",
        views=_main_view(
            "Herramientas",
            "Tools MCP extra.",
            "Registra, activa o desactiva servidores MCP que el agente puede invocar.",
        ),
        group="Agente IA",
        sort_order=54,
    ),
    AdminSectionSpec(
        id="sec-15",
        system_name="agent-audit-log",
        label="Bitácora",
        path="/agent/audit-log",
        section_type=SECTION_FUNCTIONAL,
        # ADR-022: pasa del L3 sin chat a un L2 con chat contextual propio.
        default_agent_profile_id=AGENT_SETTINGS,
        description="Historial de cambios que el agente hizo en las tablas.",
        views=_main_view(
            "Bitácora",
            "Auditoría de escrituras del agente.",
            "Revisa create/update/delete del agente y restaura un delete si hace falta.",
        ),
        related_tools=("list_recent_changes", "restore_deleted_record"),
        group="Agente IA",
        sort_order=55,
    ),
    AdminSectionSpec(
        id="sec-16",
        system_name="settings-agents",
        label="Catálogo de Agentes",
        path="/settings/agents",
        section_type=SECTION_TABLE,
        default_agent_profile_id=AGENT_CONFIGURATION,
        description="Definición y overrides de cada perfil de agente.",
        views=_crud_views(
            "Agentes",
            "Definición en código (tools, nivel) y lo editable: prompt, metodologías, "
            "secciones que gestiona, destinos de delegación y memoria propia (L1/L2).",
            False,
            allow_create=False,
        ),
        group="Settings",
        sort_order=90,
    ),
    AdminSectionSpec(
        id="sec-17",
        system_name="settings-sections",
        label="Secciones del Admin",
        path="/settings/sections",
        section_type=SECTION_FUNCTIONAL,
        default_agent_profile_id=AGENT_CONFIGURATION,
        description="Catálogo de pantallas: tipo, agente de dominio e instrucciones.",
        views=_main_view(
            "Secciones del Admin",
            "Registro de secciones operativas.",
            "Cada fila es una pantalla o área. Tipo tabla/funcional/métricas/bucket, "
            "agente con dominio, instrucciones del sidebar y descripción de vistas.",
        ),
        group="Settings",
        sort_order=91,
    ),
    AdminSectionSpec(
        id="sec-18",
        system_name="settings-agent-prompts",
        label="Prompts Globales",
        path="/settings/agent-prompts",
        section_type=SECTION_FUNCTIONAL,
        default_agent_profile_id=AGENT_CONFIGURATION,
        description="System prompt base y reglas globales que aplican a TODOS los agentes.",
        views=_main_view(
            "Prompts Globales",
            "Instrucciones base compartidas por todo el harness.",
            "System prompt global y reglas de grounding/asignación de metodologías. "
            "Los cambios aplican desde el siguiente mensaje de cualquier agente.",
        ),
        group="Settings",
        sort_order=92,
    ),
    AdminSectionSpec(
        id="sec-19",
        system_name="settings-error-reports",
        label="Reportes de Falla",
        path="/settings/error-reports",
        section_type=SECTION_TABLE,
        default_agent_profile_id=AGENT_SETTINGS,
        description="Bitácora de errores del sistema (tabla error_reports): pendientes y resueltos.",
        views=_main_view(
            "Reportes de Falla",
            "Errores capturados en cualquier parte del sistema (ADR-018).",
            "Cada fila es una falla con su origen, severidad y número de repeticiones. "
            "Filtra por estado (pendiente/resuelto) o severidad, abre el detalle para ver "
            "el traceback y el contexto, y márcala como resuelta cuando el problema ya se "
            "corrigió en el código. El chat de esta sección usa la tool error_report_settings.",
        ),
        related_tools=("error_report_settings",),
        group="Settings",
        sort_order=93,
    ),
]

# (sec-N, resource_key, label, agent_id, group, sort_order, description, singleton)
# El primer entero es el PK CONGELADO — ver la nota de numeración del módulo.
_CAREER_ROWS: List[Tuple[int, str, str, str, str, int, str, bool]] = [
    (20, "personal-profile", "Datos personales", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 100, "Ficha biográfica de referencia (nombre, contacto, idiomas).", True),
    (21, "differentiators", "Diferenciadores", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 101, "Pilares que te distinguen, con evidencia.", False),
    (22, "identity", "Identidad", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 102, "Tagline, bio y propuesta de valor comunicable.", True),
    (23, "identity-reflections", "Reflexiones de identidad", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 103, "Notas IKIGAI y material bruto de narrativa.", False),
    (24, "competencies", "Competencias", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 104, "Capacidades demostrables y su evidencia.", False),
    (25, "certifications", "Certificaciones", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 105, "Credenciales formales y syllabus.", False),
    (26, "target-roles", "Roles objetivo", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 106, "Roles a los que apuntas la búsqueda.", False),
    (27, "work-history", "Historial laboral", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 107, "Experiencia profesional cronológica.", False),
    (28, "achievements", "Logros", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 108, "Resultados concretos con métricas.", False),
    (29, "star-stories", "Historias STAR", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 109, "Historias de entrevista en formato STAR.", False),
    (30, "career-reviews", "Revisiones de carrera", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 110, "Retrospectivas periódicas de carrera.", False),
    (31, "role-gap-analysis", "Análisis de brechas", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 111, "Gaps entre tu perfil y un rol objetivo.", False),
    (32, "projects", "Proyectos", AGENT_PROFESSIONAL_IDENTITY, "Identidad Profesional", 112, "Proyectos de portafolio y evidencia técnica.", False),
    (33, "fit-scoring-factors", "Factores de fit", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 120, "Criterios ponderados para evaluar vacantes.", False),
    (34, "market-segments", "Segmentos de mercado", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 121, "Bolsas de mercado donde buscas.", False),
    (35, "role-narratives", "Narrativas de rol", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 122, "Cómo te presentas para un tipo de rol.", False),
    (36, "search-plans", "Planes de búsqueda", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 123, "Plan activo: metas, cadencia, foco.", False),
    (37, "networking-contacts", "Contactos", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 124, "Personas relevantes para la búsqueda.", False),
    (38, "target-companies", "Empresas diana", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 125, "Empresas objetivo y su priorización.", False),
    (39, "vacancies", "Vacantes", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 126, "Ofertas en seguimiento, con fit y estado.", False),
    (40, "cv-versions", "Versiones de CV", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 127, "Versiones de CV ligadas a roles o vacantes.", False),
    (41, "cover-letter-versions", "Cover letters", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 128, "Cartas de presentación versionadas.", False),
    (42, "applications", "Aplicaciones", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 129, "Postulaciones enviadas y su estado.", False),
    (43, "application-interactions", "Interacciones de aplicación", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 130, "Seguimiento de cada postulación.", False),
    (44, "interviews", "Entrevistas", AGENT_SEARCH_OPERATIONS, "Operativa de Búsqueda", 131, "Procesos de entrevista y notas.", False),
    (45, "linkedin-profile", "Perfil de LinkedIn", AGENT_DIGITAL_PRESENCE, "Presencia Digital", 140, "Traducción de identidad al formato LinkedIn.", True),
    (46, "github-profile", "Perfil de GitHub", AGENT_DIGITAL_PRESENCE, "Presencia Digital", 141, "Headline y README de perfil (no la API en vivo).", True),
    (47, "portal-home", "Portal · Home", AGENT_DIGITAL_PRESENCE, "Presencia Digital", 142, "Hero de la home del portafolio público.", True),
    (48, "portal-about", "Portal · Sobre Mí", AGENT_DIGITAL_PRESENCE, "Presencia Digital", 143, "Nombre y foto de la página Sobre Mí.", True),
    (49, "portal-contact", "Portal · Contacto", AGENT_DIGITAL_PRESENCE, "Presencia Digital", 144, "Datos de contacto y footer del portal.", True),
    (50, "publications", "Publicaciones", AGENT_DIGITAL_PRESENCE, "Presencia Digital", 145, "Artículos del blog del portafolio.", False),
    (51, "contact-interactions", "Interacciones de contacto", AGENT_NETWORKING, "Networking", 150, "Seguimiento de conversaciones con contactos.", False),
    (52, "networking-activities", "Actividades de networking", AGENT_NETWORKING, "Networking", 151, "Eventos y acciones de networking.", False),
    (53, "tags", "Tags", AGENT_SUPPORT, "Soporte", 160, "Etiquetas transversales del gestor de carrera.", False),
    (54, "operational-methodologies", "Metodologías Operativas", AGENT_METHODOLOGIES, "Soporte", 161, "Protocolos de trabajo que consultan los agentes.", False),
]

_SECTIONS.extend(_career(*row) for row in _CAREER_ROWS)

_BY_ID: Dict[str, AdminSectionSpec] = {s.id: s for s in _SECTIONS}
_BY_SYSTEM_NAME: Dict[str, AdminSectionSpec] = {s.system_name: s for s in _SECTIONS}
_BY_PATH: Dict[str, AdminSectionSpec] = {s.path: s for s in _SECTIONS}

assert len(_BY_ID) == len(_SECTIONS), "PK sec-N duplicado en el registro de secciones"
assert len(_BY_SYSTEM_NAME) == len(_SECTIONS), "system_name duplicado en el registro de secciones"

# Entero más alto asignado hasta hoy. Al añadir una sección se sube este valor y
# se le da el siguiente entero libre; los números retirados (secciones eliminadas)
# NUNCA se reutilizan. El registro nunca debe contener un sec-N por encima de esto.
_HIGH_WATER = 54

_SECTION_NUMBERS = [int(s.id.split("-")[1]) for s in _SECTIONS]
assert max(_SECTION_NUMBERS) <= _HIGH_WATER, "sec-N por encima de _HIGH_WATER: súbelo"
assert len(_SECTION_NUMBERS) == len(set(_SECTION_NUMBERS)), "entero sec-N colisionado"


def list_section_specs() -> List[AdminSectionSpec]:
    return sorted(_SECTIONS, key=lambda s: (s.sort_order, s.label))


def get_section_spec(section_id: str) -> AdminSectionSpec:
    """Busca por PK (``sec-N``)."""
    if section_id not in _BY_ID:
        raise KeyError(f"Unknown admin section: {section_id}")
    return _BY_ID[section_id]


def get_section_by_system_name(system_name: str) -> AdminSectionSpec:
    """Busca por slug legible (``dashboard``, ``career-projects``…). Migración/debug."""
    if system_name not in _BY_SYSTEM_NAME:
        raise KeyError(f"Unknown admin section (system_name): {system_name}")
    return _BY_SYSTEM_NAME[system_name]


def known_section_ids() -> set[str]:
    """PKs ``sec-N`` de todas las secciones registradas."""
    return set(_BY_ID.keys())


def match_section(route: str) -> Optional[Tuple[AdminSectionSpec, str]]:
    """Devuelve (sección, view_key) para una ruta del Admin, o None."""
    if not route:
        return None
    path = route.split("?")[0].rstrip("/") or "/"
    if path in _BY_PATH:
        spec = _BY_PATH[path]
        return spec, spec.views[0].key
    prefixes = sorted(
        (s for s in _SECTIONS if path.startswith(f"{s.path}/")),
        key=lambda s: len(s.path),
        reverse=True,
    )
    if not prefixes:
        return None
    spec = prefixes[0]
    view_keys = {v.key for v in spec.views}
    if "view" in view_keys:
        return spec, "view"
    if "record" in view_keys:
        return spec, "record"
    return spec, spec.views[-1].key


def view_for(spec: AdminSectionSpec, view_key: str) -> AdminViewSpec:
    for view in spec.views:
        if view.key == view_key:
            return view
    return spec.views[0]
