# ADR-034: Se retira el descubrimiento de vacantes

## Estado

Aceptado — 2026-11-12 (orden del propietario). Retira lo decidido en el [ADR-011](011-job-discovery-adapters.md).

## Contexto

El descubrimiento de vacantes consultaba portales y agregadores (Adzuna, Greenhouse, Lever, LinkedIn por URL, Remotive, RemoteOK y GetOnBoard). Exigía mantener al día las claves y los accesos de cada fuente, y ese mantenimiento periódico no le servía al propietario.

## Decisión

Se elimina el subsistema; el seguimiento manual de vacantes y postulaciones no cambia.

- **API:** ruta `/career/job-discoveries/*`, servicio `job_discovery/`, esquemas y pruebas; variables `ADZUNA_*` y `JOB_DISCOVERY_*`.
- **Admin:** pantalla «Descubrir vacantes» (`/job-discovery`), su entrada del menú y las llamadas de la API cliente.
- **Datos (migración `9e5a3b7d2c04`):** columnas `career_board_provider` y `career_board_token` de `target_companies`. Los valores previos (1 de 15 empresas) quedaron en un respaldo fuera del repo.
- **Se conserva:** `vacancies`, `applications`, `search_platforms` y las métricas de búsqueda.

## Consecuencias

- Las vacantes se registran a mano o con el rol `agent` por `/career/vacancies`.
- Deja de requerirse cualquier clave de portales de empleo.
- La migración tiene `downgrade` que recrea las columnas, sin sus datos.
