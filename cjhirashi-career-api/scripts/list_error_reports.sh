#!/usr/bin/env bash
# Lista reportes de falla del sistema (tabla error_reports, ADR-018).
#   ./list_error_reports.sh          -> solo pendientes
#   ./list_error_reports.sh --all    -> pendientes + resueltos
#
# Lee las credenciales de PostgreSQL del .env de la raíz del proyecto.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

WHERE="WHERE resolved = false"
[ "${1:-}" = "--all" ] && WHERE=""

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" postgres_db \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -P pager=off -c "
    SELECT id,
           severity,
           resolved,
           occurrences AS reps,
           source,
           to_char(last_seen_at, 'YYYY-MM-DD HH24:MI') AS last_seen,
           left(message, 90) AS message
      FROM error_reports
      ${WHERE}
     ORDER BY resolved ASC,
              (severity = 'critical') DESC,
              occurrences DESC,
              last_seen_at DESC;
  "
