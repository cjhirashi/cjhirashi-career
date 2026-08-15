# Documentación — MCP Tools Server

Índice centralizado de la documentación técnica, con navegación por rol, diagramas interactivos y guías detalladas.

---

## Estructura de Documentación

La documentación está organizada en **cuatro secciones principales**:

```
📚 Documentación (este README)
├── 🚀 Guía de Inicio Rápido
├── 🔌 Referencia de API
├── 🏗️ Arquitectura y Diseño
└── 🌐 Topología de Red
```

Además, hay **diagramas detallados** en la raíz de `docs/`:

- **ARCHITECTURE.md** — Componentes, flujos completos, decisiones de diseño
- **DATA_FLOW.md** — Análisis detallado de transformaciones de datos
- **NETWORK_TOPOLOGY.md** — Red Docker, puertos, volúmenes

---

## Navegar por Rol

### 👨‍💻 Soy Desarrollador (quiero entender el código)

**Orden recomendado:**

1. **[getting-started/README.md](./getting-started/README.md)** — Levantar el servidor localmente
2. **[api/README.md](./api/README.md)** — Ver qué herramientas tengo disponibles
3. **[architecture/README.md](./architecture/README.md)** — Entender cómo funciona internamente
4. **[ARCHITECTURE.md](./ARCHITECTURE.md)** — Diagramas completos con flujos detallados
5. **[../../server/README.md](../../server/README.md)** — Referencia técnica del código
6. **[../../CLAUDE.md](../../CLAUDE.md)** — Patrones de desarrollo y debugging

---

### 🏛️ Soy Arquitecto / Tech Lead (quiero entender el diseño)

**Orden recomendado:**

1. **[architecture/README.md](./architecture/README.md)** — Visión general, decisiones clave
2. **[ARCHITECTURE.md](./ARCHITECTURE.md)** — Diagramas detallados, componentes
3. **[network/README.md](./network/README.md)** — Infraestructura, topología
4. **[NETWORK_TOPOLOGY.md](./NETWORK_TOPOLOGY.md)** — Red Docker, configuración
5. **[api/README.md](./api/README.md)** — Interfaz pública, schemas
6. **[DATA_FLOW.md](./DATA_FLOW.md)** — Transformaciones, optimizaciones

---

### 🔧 Soy DevOps / SRE (quiero operar el sistema)

**Orden recomendado:**

1. **[network/README.md](./network/README.md)** — Puertos, volúmenes, seguridad
2. **[architecture/README.md](./architecture/README.md)** — Componentes, dependencias
3. **[getting-started/README.md](./getting-started/README.md)** — Setup y troubleshooting
4. **[../../docker-compose.yml](../../docker-compose.yml)** — Orquestación
5. **[../../server/mcp_tools_server.md](../../server/mcp_tools_server.md)** — Monitoreo, logs
6. **[../../CLAUDE.md](../../CLAUDE.md)** — Troubleshooting avanzado

---

### 🎨 Soy Product Manager / Diseñador (quiero entender qué hace)

**Orden recomendado:**

1. **[architecture/README.md](./architecture/README.md)** — Qué es y cómo funciona
2. **[api/README.md](./api/README.md)** — Qué herramientas hay disponibles
3. **[ARCHITECTURE.md](./ARCHITECTURE.md)** — Diagramas visuales del flujo
4. **[../../README.md](../../README.md)** — Descripción general del proyecto

---

## Tabla Completa de Documentos

| Sección | Archivo | Descripción | Público | Técnico |
|---------|---------|-------------|---------|---------|
| **Inicio Rápido** | [getting-started/README.md](./getting-started/README.md) | Instalación, uso básico, primeros pasos | ✓ | ✓ |
| **Referencia API** | [api/README.md](./api/README.md) | Herramientas MCP, schemas JSON, ejemplos | ✓ | ✓ |
| **Arquitectura** | [architecture/README.md](./architecture/README.md) | Componentes, flujos, decisiones de diseño | ✗ | ✓ |
| **Red y Config** | [network/README.md](./network/README.md) | Docker, puertos, volúmenes, seguridad | ✗ | ✓ |
| **Diagr. Arquitectura** | [ARCHITECTURE.md](./ARCHITECTURE.md) | 4 diagramas Mermaid detallados | ✗ | ✓ |
| **Flujos de Datos** | [DATA_FLOW.md](./DATA_FLOW.md) | 3 diagramas de transformación, manejo de errores | ✗ | ✓ |
| **Topología Red** | [NETWORK_TOPOLOGY.md](./NETWORK_TOPOLOGY.md) | 3 diagramas de red Docker, volúmenes | ✗ | ✓ |

---

## Búsqueda por Tarea

¿Necesitas... ?

### Levantar el Servidor

→ [getting-started/README.md](./getting-started/README.md) **Instalación y Setup**

### Entender las Herramientas Disponibles

→ [api/README.md](./api/README.md) **Tabla de Herramientas MCP**

### Generar un CV Programáticamente

→ [api/README.md](./api/README.md) **Herramienta 1: crear_cv_pdf** + [getting-started/README.md](./getting-started/README.md) **Uso Básico**

### Entender Cómo Funciona Internamente

→ [architecture/README.md](./architecture/README.md) **Flujo de Datos Completo** → [ARCHITECTURE.md](./ARCHITECTURE.md) **Diagramas**

### Configurar Puertos o Red

→ [network/README.md](./network/README.md) **Configuración de Puertos** → [docker-compose.yml](../../docker-compose.yml)

### Resolver Errores de Red

→ [network/README.md](./network/README.md) **Solución de Problemas de Red**

### Resolver Errores de Generación de PDF

→ [getting-started/README.md](./getting-started/README.md) **Solución de Problemas Comunes** → [../../CLAUDE.md](../../CLAUDE.md)

### Añadir un Nuevo Tipo de Documento

→ [architecture/README.md](./architecture/README.md) **Extensibilidad** → [../../server/README.md](../../server/README.md)

### Optimizar el Sistema

→ [architecture/README.md](./architecture/README.md) **Optimizaciones Propuestas** → [network/README.md](./network/README.md) **Configuración Avanzada**

---

## Diagramas Interactivos

Todos los diagramas usan la **paleta de colores armónica** estándar:

- **Morado (#A855F7)** — Cliente, Usuario, Interfaz
- **Verde (#10B981)** — Servidor, Procesamiento, Componentes Activos
- **Cyan (#06B6D4)** — Almacenamiento, Documentación, Persistencia
- **Gris (#9CA3AF)** — Dependencias Externas

Ver [../../COLOR_PALETTE.md](../../COLOR_PALETTE.md) para detalles completos.

### Diagramas Disponibles

**Arquitectura:**
- Diagrama de componentes general (4 bloques)
- Flujo de CV (paso a paso)
- Flujo de cover letter (paso a paso)
- Topología de red Docker
- Escalabilidad y mejoras futuras

**Red:**
- Topología Docker con puertos
- Flujo de solicitudes HTTP
- Bind volumes y persistencia

Ver [ARCHITECTURE.md](./ARCHITECTURE.md), [DATA_FLOW.md](./DATA_FLOW.md), [NETWORK_TOPOLOGY.md](./NETWORK_TOPOLOGY.md) para todos los diagramas.

---

## Guía Rápida de Referencias Cruzadas

```
getting-started/
├─ Instalar → network/ (puertos, volúmenes)
├─ Usar → api/ (herramientas disponibles)
└─ Troubleshoot → ../../CLAUDE.md (debugging avanzado)

api/
├─ Esquema JSON → architecture/ (flujos)
├─ Respuestas → getting-started/ (testing)
└─ Extensiones → architecture/ (agregar herramientas)

architecture/
├─ Componentes → ARCHITECTURE.md (diagramas)
├─ Flujos → DATA_FLOW.md (transformaciones)
├─ Red → network/ + NETWORK_TOPOLOGY.md
└─ Código → ../../server/README.md

network/
├─ Puertos → docker-compose.yml
├─ Volúmenes → ../../server/README.md
└─ Troubleshoot → getting-started/ (errores comunes)
```

---

## Estadísticas de Documentación

| Métrica | Valor |
|---------|-------|
| **Secciones README** | 4 (getting-started, api, architecture, network) |
| **Documentos técnicos** | 7 (include ARCHITECTURE.md, DATA_FLOW.md, etc.) |
| **Diagramas Mermaid** | 10+ |
| **Ejemplos de código** | 15+ |
| **Referencias cruzadas** | 50+ |
| **Checklist de setup** | 3 |

---

## Mantener la Documentación Actualizada

### Cuando Cambies...

| Si cambias... | Actualiza... | Prioridad |
|---------------|-------------|----------|
| Puertos en docker-compose.yml | network/README.md + NETWORK_TOPOLOGY.md | Alta |
| Lógica de generación de PDF | architecture/README.md + ARCHITECTURE.md | Alta |
| Estructura JSON | api/README.md | Alta |
| Diseño de templates | getting-started/README.md (ejemplos) | Media |
| Dependencias Python | ../../server/README.md | Media |
| Paleta de colores | COLOR_PALETTE.md + todos los diagramas | Baja |

### Workflow

1. **Modifica el código** → `server/`, `frontend/`
2. **Actualiza diagramas** → Si cambia arquitectura, edita `.md` en `docs/`
3. **Verifica references** → Asegúrate de que links estén correctos
4. **Commit** → Incluye cambios de documentación

---

## Feedback y Mejoras

Encontraste un error o tienes una sugerencia?

**Reportar:**
- Errores de documentación → Crear issue con etiqueta `docs`
- Sugerir mejoras → Crear issue con etiqueta `enhancement`
- Actualizar → Pull request directo con cambios

**Contacto:** Carlos (cjhirashi@gmail.com)

---

## Recursos Externos

- **[Model Context Protocol Docs](https://modelcontextprotocol.io)** — Especificación MCP
- **[FastMCP Framework](https://github.com/jlowin/fastmcp)** — Documentación de FastMCP
- **[WeasyPrint Docs](https://doc.courtbouillon.org/weasyprint/)** — Renderizado de PDF
- **[Jinja2 Template Docs](https://jinja.palletsprojects.com/)** — Template engine
- **[Docker Compose Docs](https://docs.docker.com/compose/)** — Orquestación

---

**Última actualización:** 2026-08-15  
**Versión de documentación:** 2.0 (Modular)  
**Estatus:** ✓ Completo y coherente  
**Contacto:** Carlos (cjhirashi@gmail.com)
