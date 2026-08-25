# ADR-013: L3 consulta web y L3 GitHub (solo lectura)

## Estado

Aceptado — 2026-08-25

Extiende el catálogo de [ADR-012](./012-bedrock-three-level-agents.md) sin cambiar las reglas de jerarquía (L1/L2 hablan; L3 ejecuta; delegación solo hacia abajo).

## Contexto

Los especialistas L1/L2 alucinaban fuentes o el estado de un repo porque no tenían tools de red. Había un `github_service` solo para listar repos públicos del username de `github-profile` (Admin, sin PAT). Hacía falta un oficio de **consulta web** y otro de **consulta a repositorios GitHub**, sin mezclarlos con CRUD de carrera ni con publicación LinkedIn.

## Decisión

Dos workers L3, sin chat:

| Perfil | Oficio | Tools | Conexión |
|--------|--------|-------|----------|
| `agent_web_search` | Buscar y leer páginas públicas | `web_search`, `web_fetch` | Brave Search si hay `BRAVE_SEARCH_API_KEY`; si no, DuckDuckGo HTML. `web_fetch` con defensa SSRF. |
| `agent_github` | Estado de conexión y lectura de repos | `get_github_status`, `list_github_repos`, `get_github_repo`, `list_github_contents`, `get_github_file`, `search_github_code` | `GITHUB_TOKEN` (PAT). Sin token: solo repos públicos del username en `github-profile`. |

Reglas:

- L1 y cualquier L2 delegan a estos L3 (misma regla ADR-012).
- L2 `agent_digital_presence` sigue siendo dueño de `github-profile` (ficha CRUD). La API live es L3.
- Solo lectura en GitHub: no issues, PRs ni pushes.
- `web_fetch` rechaza `localhost`, IPs privadas, metadata y esquemas que no sean http/https.

### Por qué

- Un agente, una responsabilidad: buscar en la web no es el oficio de búsqueda de vacantes; GitHub live no es el CRUD de presencia digital.
- PAT en entorno (no OAuth) es suficiente para un operador único; LinkedIn sí exige OAuth porque la API de posts lo pide.
- SSRF es innegociable si el modelo puede pedir URLs.

## Consecuencias

### Positivas

- L1/L2 pueden citar páginas y archivos de repo con evidencia de tool.
- El Admin no gana una superficie de chat L3 (los labels solo aparecen en delegación).

### Costos

- DuckDuckGo HTML puede fallar desde IPs de datacenter; Brave es el camino fiable.
- Un PAT mal scoped puede leer más repos de los previstos (mitigación: fine-grained, Contents Read).

### Alternativas rechazadas

- Meter `web_search` en L2 search_operations: mezcla vacantes/CVs con internet abierto.
- OAuth GitHub como LinkedIn: sobreingenería para un solo usuario con PAT.
- Un solo L3 “integraciones externas”: viola SRP.

## Referencias

- Harness: `api/src/services/bedrock/agent_profiles.py`, `tools.py`
- Clientes: `api/src/services/web_search_service.py`, `api/src/services/github_service.py`
- Espejo UI: `admin/src/config/agentProfiles.ts`
- [ADR-012](./012-bedrock-three-level-agents.md)

---

**Creado por**: Arquitecto de Soluciones  
**Fecha de creación**: 2026-08-25  
**Estado de vigencia**: Vigente
