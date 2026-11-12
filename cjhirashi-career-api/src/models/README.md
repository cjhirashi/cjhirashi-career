# Paquete `models/`

ORM SQLAlchemy 2.0. Todas las clases heredan de `database.Base`. IDs de negocio son `String(20)` prefijados (`register_id_listener`). Filas de carrera llevan `user_id` con `ON DELETE CASCADE`.

`__init__.py` reexporta todos los modelos para Alembic (`import models`) y tests.

## Arquitectura

```mermaid
flowchart TB
    Base[database.Base] --> Core[user / refresh_token / file_upload / audit]
    Base --> Identity[Identidad — 12 modelos]
    Base --> Search[Búsqueda — 14 modelos]
    Base --> Digital[Digital — portal / publications / perfiles]
    Base --> Support[tag / operational_methodology]
    Base --> Agent[bedrock_* / pdf_*]
    Core --> PG[(PostgreSQL)]
    Identity --> PG
    Search --> PG
    Digital --> PG
    Support --> PG
    Agent --> PG
    Identity -.->|user_id CASCADE| Core
    Search -.->|user_id CASCADE| Core
```

---

## Núcleo y seguridad

| Módulo | Tabla / clase | Función |
|--------|---------------|---------|
| `user.py` | `User` | Cuenta: username, email, hash, perfil, `is_active` |
| `refresh_token.py` | `RefreshToken` | Refresh JWT persistido / revocable |
| `user_session.py` | `UserSession` | Sesiones de login (tracking) |
| `file_upload.py` | `FileUpload`, `FileType` | Metadatos MinIO (categoría, visibilidad, MIME) |
| `audit_log.py` | `AuditLog`, `AuditAction` | Bitácora create/update/delete (también restore del agente) |
| `event.py` | `Event`, `EventType` | Eventos de actividad de usuario |
| `metrics.py` | `Metrics` | Snapshot de métricas de perfil |

---

## Carrera — Identidad

| Módulo | Contenido |
|--------|-----------|
| `differentiator.py` | Pilares de diferenciación + evidencia |
| `identity.py` | Singleton: tagline, bio, UVP (1:1 con User) |
| `identity_reflection.py` | Reflexiones IKIGAI (pasión, profesión, vocación, misión) |
| `competencies.py` | Competencias técnicas / transferibles / negocio |
| `certification.py` | Certificaciones (syllabus Markdown, `document_url`, status) |
| `target_role.py` | Roles objetivo de la búsqueda |
| `work_history.py` | Historial laboral |
| `achievement.py` | Logros (reto / solución / impacto) |
| `star_story.py` | Historias STAR 60–90 s |
| `career_review.py` | Revisiones periódicas / transiciones |
| `role_gap_analysis.py` | Gaps vs rol objetivo |
| `project.py` | Proyectos de portafolio (featured, portal) |

---

## Carrera — Búsqueda

| Módulo | Contenido |
|--------|-----------|
| `fit_scoring_factor.py` | Factores ponderados de fit de vacante |
| `market_segment.py` | Canales mercado visible/oculto |
| `role_narrative.py` | Narrativas reutilizables por rol |
| `search_plan.py` | Planes semanales de búsqueda |
| `networking_contact.py` | Red profesional |
| `contact_interaction.py` | Log de comunicación con un contacto |
| `networking_activity.py` | Actividades give/share/talk |
| `target_company.py` | Empresas objetivo |
| `vacancy.py` | Vacantes trackeadas |
| `cv_version.py` | CV versionado (Markdown `content`) |
| `cover_letter_version.py` | Cartas versionadas |
| `application.py` | Postulaciones a una vacante |
| `application_interaction.py` | Log de comunicación de la postulación |
| `interview.py` | Entrevistas por postulación |

---

## Carrera — Digital, soporte, metodologías

| Módulo | Contenido |
|--------|-----------|
| `publication.py` | Posts/blog (alimenta `/public` blog) |
| `linkedin_profile.py` | Staging del perfil LinkedIn (no OAuth) |
| `github_profile.py` | Username + copy; repos se piden en vivo |
| `portal_home.py` | Hero y stats del Home público |
| `portal_about.py` | Copy extra de Sobre mí (bio vive en `identity`) |
| `portal_contact.py` | Contacto + footer (links sociales salen de perfiles) |
| `portal_site.py` · `portal_visitor.py` · `portal_visit.py` | Analítica del portafolio: sitios medidos, visitantes seudónimos y visitas (SPEC-0010) |
| `portal_event.py` | Eventos crudos de tráfico (ampliado con `site_id`, `visitor_id`, `visit_id`, `seq`, `props`) |
| `portal_goal.py` · `portal_funnel.py` · `portal_annotation.py` · `portal_channel_rule.py` · `portal_daily.py` | Metas, embudos, anotaciones, reglas de canal y resumen diario |
| `tag.py` | Etiquetas transversales |
| `operational_methodology.py` | Protocolos Markdown + `agent_profile_ids` (agentes destinatarios) |

---

## Bedrock y PDF

| Módulo | Contenido |
|--------|-----------|
| `bedrock_settings.py` | Fila única: modelo, presupuesto, prompt override, límites |
| `bedrock_agent_profile_prompt.py` | Suffix editable por perfil de agente |
| `bedrock_custom_tool.py` | Servidores MCP remotos registrados |
| `bedrock_conversation.py` | `BedrockConversation` + `BedrockConversationMessage` (historial por `session_type` + `agent_profile_id`) |
| `bedrock_usage_log.py` | Costo/tokens por turno |
| `bedrock_usage_round_log.py` | Costo granular (Converse, tool, imagen) |
| `bedrock_task.py` | Tareas/plan del agente (`/agent-tasks`) |
| `pdf_output_template.py` | Plantillas HTML → PDF |
| `pdf_template_style.py` | CSS reutilizable (`style_id`) |

---

---

## Operación del Admin, agentes y contacto (añadidos después del diseño inicial)

| Modelo | Tabla | Rol |
|---|---|---|
| `AdminSectionOverride` | `admin_section_overrides` | Overrides editables de una sección del Admin: agente L2 del chat contextual, instrucciones y vistas |
| `UserNotification` | `user_notifications` | Avisos in-app (ADR-016): turnos de tareas y mensajes de contacto |
| `ErrorReport` | `error_reports` | Registro centralizado de fallas con huella para deduplicar (ADR-018) |
| `ContactMessage` | `contact_messages` | Mensajes del formulario de contacto del portafolio |
| `BedrockAgentDelegation` | `bedrock_agent_delegation` | Destinos de delegación editables por perfil (subconjunto de los permitidos por nivel) |
| `BedrockAgentProfilePhoto` | `bedrock_agent_profile_photos` | Foto de un agente del catálogo, elegida del bucket MinIO |
| `BedrockAgentProfileTool` | `bedrock_agent_profile_tools` | Override de herramientas por perfil de agente |
| `PersonalProfile` | `personal_profile` | Hechos biográficos de referencia para los agentes |
| `SearchPlatform` | `search_platforms` | Plataformas de búsqueda de empleo donde Carlos tiene cuenta (LinkedIn, GetOnBoard…) |
