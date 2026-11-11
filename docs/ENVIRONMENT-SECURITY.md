# Variables de entorno y secretos

**Última actualización**: 2026-11-05

Cómo se configura y protege el entorno del sistema. Complementa [07-DEPLOYMENT-VIEW.md](./07-DEPLOYMENT-VIEW.md) y [08-CROSSCUTTING-CONCEPTS.md](./08-CROSSCUTTING-CONCEPTS.md).

## Estrategia

| Archivo | En git | Contenido |
|---|---|---|
| `docker-compose.yml` | Sí | Estructura de servicios; **solo referencias** `${VARIABLE}`, nunca valores |
| `.env.example` | Sí | Plantilla autodescriptiva sin secretos reales |
| `.env` | **No** (ignorado) | Valores reales. Lo lee el compose (`env_file: .env` en `api`, `postgres` y `minio`) |

Producción usa el mismo mecanismo: un `.env` en el servidor, fuera del repo. No hay despliegue por GitHub Actions (el CI solo corre pruebas) ni «GitHub Secrets» de producción.

```bash
cp .env.example .env     # primera vez
$EDITOR .env             # valores reales
docker compose up -d --build
```

## Variables

Todas las lee la API (`cjhirashi-career-api/src/config.py`) salvo las de PostgreSQL y MinIO, que también las usan sus contenedores. El Admin recibe solo `VITE_API_BASE_URL=/api` y el Portal, `VITE_API_URL=/api`.

| Grupo | Variables | Notas |
|---|---|---|
| PostgreSQL | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL` | El compose compone `DATABASE_URL` para el contenedor de la API; la de `.env` sirve para ejecutar fuera de Docker |
| Seguridad | `SECRET_KEY` (**obligatoria**, 32+ caracteres aleatorios), `ALGORITHM` (`HS256`), `ACCESS_TOKEN_EXPIRE_DAYS` (7) | Cambiar `SECRET_KEY` invalida todos los tokens emitidos |
| CORS | `CORS_ORIGINS` | Lista separada por comas, sin espacios; la plantilla trae solo `localhost` |
| Aplicación | `APP_NAME`, `APP_VERSION`, `DEBUG`, `UPLOADS_DIR`, `MAX_UPLOAD_SIZE_MB` | `DEBUG=true` baja el nivel de logs a DEBUG; no lo dejes activo en producción. `LOG_LEVEL` aparece en `.env.example` pero la API no lo lee |
| MinIO | `MINIO_ENDPOINT` (`minio:9000`, nombre del servicio, no `localhost`), `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_BUCKET`, `MINIO_PUBLIC_URL` | Un valor `localhost` filtrado desde el entorno del host deja sin almacenamiento de archivos a la API (el resto sigue sirviendo) |
| Descubrimiento de vacantes | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `ADZUNA_COUNTRY`, `JOB_DISCOVERY_TIMEOUT_SECONDS`, `JOB_DISCOVERY_MAX_RESULTS` | Claves gratuitas de Adzuna; los demás adaptadores no requieren clave |
| Agentes: herramientas | `GITHUB_TOKEN`, `BRAVE_SEARCH_API_KEY` | Lectura de repositorios y consulta web del agente |
| Portal | `PUBLIC_PORTAL_USER_ID`, `PORTAL_SITE_KEY` | Usuario dueño del portafolio público y clave del sitio para la analítica |

## Reglas

1. **Nunca** versionar `.env` ni valores reales; `docker-compose.yml` solo usa `${VARIABLE}`.
2. Cada secreto es único por entorno: no reutilices claves entre desarrollo y producción.
3. Las credenciales de AWS deben tener permisos acotados a Bedrock; su rotación y el alcance del rol IAM son un riesgo abierto ([11-TECHNICAL-RISKS.md](./11-TECHNICAL-RISKS.md)).
4. La API no se publica al host: se alcanza por la red Docker y por `/api/` de los hosts públicos.
5. Los archivos de la base de datos y de MinIO viven fuera del repo (`/mnt/disco1/cjhirashi-data/cjhirashi-career-volumes/`).

## Comprobaciones

```bash
git ls-files | grep -E '^\.env$'        # debe salir vacío
git check-ignore -v .env                # debe mostrar la regla de .gitignore
grep -nE 'PASSWORD:|SECRET_KEY:' docker-compose.yml   # solo referencias ${…}
```

## Si se commitea un secreto por error

1. **Rotarlo de inmediato**: contraseña de la base de datos, `SECRET_KEY` (invalida los tokens), claves de AWS en IAM o `MINIO_ROOT_PASSWORD`.
2. Retirarlo del historial si el repo se comparte (`git filter-repo`) y empujar el arreglo.
3. Revisar los registros de acceso del servicio afectado.

## Checklist de arranque seguro

- [ ] `.env` creado desde `.env.example` y ausente de `git ls-files`
- [ ] `SECRET_KEY` de 32+ caracteres aleatorios
- [ ] Contraseñas de PostgreSQL y MinIO propias
- [ ] `CORS_ORIGINS` con los orígenes reales del entorno
- [ ] Credenciales de AWS con permisos mínimos y `BEDROCK_DAILY_BUDGET_USD` definido
- [ ] `DEBUG=false` en producción
