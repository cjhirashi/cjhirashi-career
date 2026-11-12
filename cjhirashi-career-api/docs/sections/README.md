# Documentación por sección — API REST

Índice de READMEs detallados. Cada sección documenta endpoints, schemas, servicios, flujos y ejemplos de uso.

## Arquitectura

```mermaid
flowchart TB
    subgraph Acceso
        Auth[auth]
        Infra[infrastructure]
    end
    subgraph Carrera
        Ident[career-identity]
        Search[career-search]
        Digital[career-digital]
        Support[career-support]
        Metrics[career-metrics]
        Methods[career-methodologies]
    end
    subgraph Doc["Tareas y PDF"]
        Tasks[bedrock-tasks]
        PDF[pdf-templates]
        Styles[pdf-template-styles]
    end
    subgraph Ext
        Files[files]
        Public[public]
        PortalA[portal-analytics]
    end
    Auth --> Carrera
    Infra --> Carrera
    Infra --> Agente
    Infra --> Ext
```

---

## Autenticación y acceso

| Sección | Descripción |
|---------|-------------|
| [auth](auth/README.md) | Login, registro, refresh token, perfil, cambio de contraseña |
| [infrastructure](infrastructure/README.md) | JWT middleware, CRUD factory, repositorios, IDs prefijados |

---

## Dominio Carrera (JWT requerido)

| Sección | Recursos | Endpoints |
|---------|----------|-----------|
| [career-identity](career-identity/README.md) | Identidad, competencias, logros, proyectos… | 12 recursos CRUD |
| [career-search](career-search/README.md) | Vacantes, aplicaciones, entrevistas, CVs… | 14 recursos CRUD + PDF |
| [career-digital](career-digital/README.md) | Portal, publicaciones, perfiles sociales | 6 recursos CRUD + GitHub |
| [career-support](career-support/README.md) | Etiquetas transversales | 1 recurso CRUD |
| [career-metrics](career-metrics/README.md) | Métricas semanales y overview de búsqueda | 2 endpoints read-only |
| [career-methodologies](career-methodologies/README.md) | Metodologías operativas | 1 recurso CRUD |

---

## Agente IA y documentos

| Sección | Descripción |
|---------|-------------|
| [bedrock-tasks](bedrock-tasks/README.md) | Tablero de tareas de Carlos |
| [pdf-templates](pdf-templates/README.md) | Plantillas HTML → tabla `pdf_output_templates` |
| [pdf-template-styles](pdf-template-styles/README.md) | Estilos CSS → tabla `pdf_template_styles` |

---

## Integraciones y almacenamiento

| Sección | Descripción |
|---------|-------------|
| [files](files/README.md) | Upload, presigned URLs, MinIO |

---

## Portal público (sin autenticación)

| Sección | Descripción |
|---------|-------------|
| [public](public/README.md) | Home, About, Projects, Blog, Contact |

---

## Cómo leer cada README

Cada documento de sección sigue esta estructura:

1. **Propósito** — qué problema resuelve
2. **Archivos fuente** — routes, schemas, services, models
3. **Endpoints** — método, path, auth, request/response
4. **Flujos** — secuencias típicas de uso
5. **Relaciones** — con otras secciones (Portal, etc.)
6. **Ejemplos curl** — peticiones representativas

---

## Implementación (paquetes `src/`)

Los README de sección documentan el **contrato HTTP**. El código interno está en:

- [src/README.md](../../src/README.md) — mapa de capas
- [src/routes/README.md](../../src/routes/README.md) — cada router
- [src/services/README.md](../../src/services/README.md) — servicios e integraciones

Volver al [README principal de la API](../README.md).

- [portal-analytics](portal-analytics/README.md) — analítica del portafolio público: visitas, canales, metas, embudos y API para agentes (SPEC-0010)
