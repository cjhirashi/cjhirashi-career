# ADR-011: Descubrimiento de vacantes por adaptadores (sin scraping)

## Estado

Aceptado

## Contexto

El dominio de carrera ya registra vacantes a mano (`vacancies.source`, `vacancies.vacancy_url`). Hacía falta descubrir ofertas en portales (Indeed, LinkedIn, Get on Board y otros) para que Carlos y Agent Bedrock alimenten el triage. Indeed y LinkedIn no ofrecen API pública de búsqueda para candidatos.

## Decisión

Un `JobDiscoveryService` dentro de la API REST, con un adaptador por portal. Preview-then-save: la búsqueda no escribe `vacancies`. Indeed es un provider lógico respaldado por Adzuna. LinkedIn solo construye URLs oficiales de `jobs/search`; las vacantes concretas entran por `import-url`. No se scrapea Indeed.com ni LinkedIn.com.

### Por Qué

- La API REST es el orquestador único (ADR implícito del alcance de portafolio).
- Un adaptador por fuente permite sumar Remotive, RemoteOK o boards Greenhouse/Lever sin tocar Admin ni Bedrock.
- Adzuna es el único canal legal para resultados estilo Indeed.
- LinkedIn no tiene proxy oficial; el agente puede orientar la búsqueda y luego importar `jobs/view`.

## Consecuencias

### Positivas

- El agente llama `run_job_discovery(providers=['indeed'|'linkedin'|…])` por nombre de producto.
- Un portal caído no tumba la búsqueda.
- El agente no persiste hasta que Carlos autoriza refs (`L1`, `L3`) o marca en Admin. Las vacantes entran como `pending_review` para seguimiento.

### Negativas

- Indeed requiere `ADZUNA_APP_ID` / `ADZUNA_APP_KEY`.
- LinkedIn no lista vacantes, solo URLs de búsqueda.

## Alternativas Consideradas

### Scraping o RapidAPI/JSearch

Rechazado: ToS, bloqueos e inestabilidad.

### Contenedor job-aggregator

Rechazado: viola el orquestador único.

## Implicaciones

- [x] Endpoints `/career/job-discoveries/*`
- [x] Tools Bedrock en perfil `search`
- [x] Campos `career_board_*` en `target_companies`

## Seguimiento

Ninguno.

---

**Creado por**: Arquitecto de Soluciones
**Fecha de creación**: 2026-08-23
**Estado de vigencia**: Vigente
