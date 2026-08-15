# Índice de Documentación Técnica — MCP Tools Server

Bienvenido a la documentación técnica del proyecto MCP Tools Server. Esta carpeta contiene diagramas interactivos, análisis de flujo y configuración de red.

---

## Navegación Rápida

### Entender la Arquitectura
Empieza aquí para visualizar cómo funciona el sistema:

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** — Diagrama general del sistema con componentes y decisiones de diseño
  - Componentes: Cliente (Morado), Servidor (Verde), Almacenamiento (Cyan)
  - Flujo de datos en secuencias
  - Topología de red Docker
  - Escalabilidad y mejoras propuestas

### Entender los Flujos de Datos
Aprende cómo se procesan CV y cover letters:

- **[DATA_FLOW.md](./DATA_FLOW.md)** — Análisis detallado de operaciones
  - Flujo de generación de CV (paso a paso)
  - Flujo de generación de cover letter
  - Estructuras de datos (JSON, transformaciones)
  - Manejo de errores y excepciones
  - Optimizaciones propuestas

### Entender la Red y Volúmenes
Configuración técnica de Docker y conectividad:

- **[NETWORK_TOPOLOGY.md](./NETWORK_TOPOLOGY.md)** — Red, puertos y almacenamiento
  - Diagrama de topología general
  - Configuración de puertos (8002 host → 8000 contenedor)
  - Bind volumes (persistencia)
  - Flujo de solicitudes HTTP
  - Seguridad de red y monitoreo

---

## Paleta de Colores

Todos los diagramas usan una **paleta armónica coherente**:

- **Morado (#A855F7)** — Clientes, usuarios, interfaz
- **Verde (#10B981)** — Servidores, procesamiento, componentes activos
- **Cyan (#06B6D4)** — Almacenamiento, documentación, persistencia
- **Gris (#9CA3AF)** — Dependencias externas

Ver **[../COLOR_PALETTE.md](../COLOR_PALETTE.md)** para detalles completos, gradientes y uso en CSS variables.

---

## Guía de Lectura Recomendada

**Según tu rol:**

### Arquitecto / Tech Lead
1. [ARCHITECTURE.md](./ARCHITECTURE.md) — Visión general
2. [NETWORK_TOPOLOGY.md](./NETWORK_TOPOLOGY.md) — Infraestructura
3. [DATA_FLOW.md](./DATA_FLOW.md) — Flujos y optimizaciones

### Developer / Ingeniero
1. [DATA_FLOW.md](./DATA_FLOW.md) — Entender el flujo de datos
2. [ARCHITECTURE.md](./ARCHITECTURE.md) — Componentes e interfaces
3. [../server/README.md](../server/README.md) — Referencia técnica del servidor
4. [../server/mcp_tools_server.md](../server/mcp_tools_server.md) — Operaciones

### DevOps / SRE
1. [NETWORK_TOPOLOGY.md](./NETWORK_TOPOLOGY.md) — Configuración de red
2. [ARCHITECTURE.md](./ARCHITECTURE.md) — Componentes y dependencias
3. [../docker-compose.yml](../docker-compose.yml) — Configuración de orquestación
4. [../server/mcp_tools_server.md](../server/mcp_tools_server.md) — Monitoreo y logs

### Product Manager / Designer
1. [ARCHITECTURE.md](./ARCHITECTURE.md) — Cómo funciona el sistema
2. [DATA_FLOW.md](./DATA_FLOW.md) — Flujo de generación de documentos
3. [../server/README.md](../server/README.md) — Ejemplos de uso

---

## Tabla de Contenidos Completa

| Documento | Descripción | Diagramas | Para Quién |
|-----------|-------------|-----------|-----------|
| **ARCHITECTURE.md** | Sistema completo, componentes, decisiones | 4 (general, secuencia, topología, escalabilidad) | Todos |
| **DATA_FLOW.md** | Procesos, transformaciones, errores | 3 (CV, cover, transformaciones) | Developers, Architects |
| **NETWORK_TOPOLOGY.md** | Red Docker, puertos, volúmenes | 3 (topología, volúmenes, flujo HTTP) | DevOps, Architects |
| **../COLOR_PALETTE.md** | Paleta de colores y su uso | Tokens y ejemplos | Documentación, Design |

---

## Modificar y Extender la Documentación

### Agregar un Nuevo Diagrama

1. Edita el archivo `.md` correspondiente
2. Usa bloques Mermaid:
   ```markdown
   ```mermaid
   graph TD
     A["Elemento Morado<br/>#A855F7"]
     B["Elemento Verde<br/>#10B981"]
     A --> B
     style A fill:#A855F7,stroke:#9333EA,stroke-width:2px,color:#fff
     style B fill:#10B981,stroke:#059669,stroke-width:2px,color:#fff
   ```
   ```
3. Sigue la paleta en [../COLOR_PALETTE.md](../COLOR_PALETTE.md)
4. Documenta qué muestra el diagrama en texto antes/después

### Actualizar Referencias Cruzadas

- Si creas un nuevo archivo, agrégalo a:
  1. Este INDEX.md
  2. [../README.md](../README.md) sección Documentación
  3. [../CLAUDE.md](../CLAUDE.md) sección de referencias

---

## Historias de Cambio

**2026-08-15**: Creación de documentación técnica completa
- Diagramas interactivos Mermaid con paleta armónica
- Análisis de flujos y topología de red
- Paleta de colores semántica

---

## Soporte y Contacto

- **Mantenedor de documentación**: Carlos (cjhirashi@gmail.com)
- **Reportar errores de documentación**: Ver [../README.md](../README.md)
- **Sugerir mejoras**: Crear issue con etiqueta `docs`

---

**Última actualización**: 2026-08-15  
**Versión**: 1.0
