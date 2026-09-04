# ADR-023: Retirar el MCP Server del alcance activo

## Estado

Aceptado — 2026-09-04

Revisa parcialmente [ADR-014](./014-four-application-modules.md) (de cuatro módulos de
aplicación a tres).

## Contexto

El `cjhirashi-career-mcp` (contenedor `cjhirashi-career-mcp`, host `mcp.cjhirashi.com`,
stack `mcp`/FastMCP + WeasyPrint) se arrastra desde el alcance anterior del proyecto
(generador de CV/Cover Letter en PDF). En el rediseño de carrera profesional se
conservó como "Canal 3 — agentes de IA externos", pero:

- Su alcance real hoy es el heredado: sólo `crear_cv_pdf` y `crear_cover_letter_pdf`.
  El CRUD de carrera vía MCP estaba **diferido** (Q4 2026) y nunca se implementó.
- La generación de PDF ya vive **in-process en la API** (WeasyPrint, ver ADR-014).
  El MCP no aporta ninguna capacidad que la API no cubra.
- No hay ningún cliente MCP consumiéndolo. El canal no tiene tráfico.
- Mantenerlo cuesta: build de imagen, un contenedor más en Compose, una entrada en
  el contrato `caddy.json`, un host y una ruta de túnel en `cjhirashi-srv`, y ruido
  en el gate y en toda la documentación arc42 (aparece como uno de los tres canales
  centrales del sistema).

Coste de mantener > valor entregado. Se decide retirarlo.

## Decisión

**Se retira `cjhirashi-career-mcp` del alcance activo del proyecto.**

- Se elimina la carpeta `cjhirashi-career-mcp/` del árbol (queda en el historial de
  git; recuperable con `git revert` / checkout del commit).
- Se elimina el servicio `mcp` de `docker-compose.yml`.
- Se elimina la entrada `mcp` del bloque `servicios` de `caddy.json` y se solicita a
  `cjhirashi-srv` (mensaje `MSG-0003`) retirar `hosts.mcp`, la ruta de túnel y el DNS
  de `mcp.cjhirashi.com`.
- Se elimina el origen `http://localhost:8004` de la configuración CORS de la API
  (`.env`, `.env.example`, `src/config.py`) — era vestigial: un cliente MCP no hace
  preflight CORS de navegador.
- El sistema pasa de **tres canales** (Portal Público, Admin Panel, MCP Server) a
  **dos** (Portal Público, Admin Panel). Agent Bedrock sigue siendo una capacidad
  interna del Admin Panel, no un canal.
- El sistema pasa de **cuatro módulos de aplicación** (ADR-014) a **tres**:
  `cjhirashi-career-admin`, `cjhirashi-career-portfolio`, `cjhirashi-career-api`.
  (`cjhirashi-career-ai` es un microservicio de apoyo, no un canal de producto.)

### Por qué retirar y no subordinar

Subordinar el MCP al Admin Panel (como Agent Bedrock) no tiene sentido: no hay una
herramienta MCP de carrera que ofrecer, y la única capacidad real (PDF) ya está en la
API. No queda nada que subordinar.

## Consecuencias

### Positivas

- Un contenedor menos, una imagen menos que construir, un host menos que exponer.
- El contrato `caddy.json` y el `docker-compose.yml` reflejan lo que realmente corre.
- La documentación de arquitectura deja de describir un canal inexistente.
- Menos superficie de ataque (un puerto expuesto menos).

### Negativas / a asumir

- El diseño objetivo del arc42 (secciones 01, 04, 05, 07, 08, 10, 12) describe el MCP
  Server como uno de los tres canales centrales. Este ADR es el registro autoritativo
  de su retiro; los arc42 llevan un aviso al inicio apuntando aquí y la reescritura
  narrativa completa queda como tarea de documentación pendiente.
- Si en el futuro se quiere exponer carrera profesional a agentes de IA externos vía
  MCP, hay que reintroducir el canal con un ADR nuevo que revierta este — idealmente
  con las herramientas de carrera ya definidas, no como el stub de PDF heredado.

## Alternativas consideradas

### Dejarlo corriendo sin tocar

- Contra: sigue el ruido en gate, contrato, docs y despliegue por un canal sin uso.

### Conservar la carpeta pero sacarlo del stack

- Contra: código muerto en el árbol que el gate y los agentes siguen viendo. Si se
  necesita, el historial de git lo tiene. Se descartó a favor de eliminar la carpeta.

## Implicaciones

- [x] `git rm -r cjhirashi-career-mcp/`
- [x] Quitar el servicio `mcp` de `docker-compose.yml`
- [x] Quitar `servicios[mcp]` de `caddy.json` + `MSG-0003` a `cjhirashi-srv`
- [x] Quitar `:8004` de CORS (`.env`, `.env.example`, `cjhirashi-career-api/src/config.py`)
- [x] Actualizar `AGENTS.md`, `README.md`, `.harness/constitution.md` (Art. 1, 2, 6)
- [x] Revisar `ADR-014` (cuatro módulos → tres)
- [x] Aviso de estado en arc42 01/04/05/07/08/10/12 apuntando a este ADR
- [ ] `cjhirashi-srv` cierra `MSG-0003` retirando `hosts.mcp` + ruta de túnel + DNS
- [ ] Reescritura narrativa completa del arc42 sin el Canal 3 (tarea de doc aparte)

## Seguimiento

Depreca la lectura de "tres canales" / "MCP Server" / "cuatro módulos" en `README`,
`AGENTS.md`, `CLAUDE.md` y arc42 a partir de 2026-09-04.

---

**Creado por**: Arquitecto de Soluciones
**Aprobado por**: Carlos Jiménez Hirashi
**Fecha de creación**: 2026-09-04
**Última revisión**: 2026-09-04
**Estado de vigencia**: Vigente
