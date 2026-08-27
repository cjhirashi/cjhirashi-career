#!/usr/bin/env bash
# Marca un reporte de falla como resuelto (o lo reabre).
#
#   ./resolve_error_report.sh err-3 "corregido: valida el payload antes de guardar (commit abc123)"
#   ./resolve_error_report.sh err-3 --reopen
#
# Escribe vía PostgreSQL directo (mismo efecto que el PATCH del Admin) para no
# depender de credenciales de la API. Credenciales de PostgreSQL del .env raíz.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
[ -f "$ENV_FILE" ] && set -a && . "$ENV_FILE" && set +a

REPORT_ID="${1:-}"
if [ -z "$REPORT_ID" ]; then
  echo "uso: $0 <err-N> \"<notas de resolución>\" | $0 <err-N> --reopen" >&2
  exit 1
fi

if [ "${2:-}" = "--reopen" ]; then
  SQL="UPDATE error_reports
          SET resolved = false, resolved_at = NULL,
              resolved_by = NULL, resolution_notes = NULL
        WHERE id = '${REPORT_ID}';"
else
  NOTES="${2:-corregido}"
  NOTES_ESCAPED="${NOTES//\'/\'\'}"
  SQL="UPDATE error_reports
          SET resolved = true, resolved_at = now(),
              resolved_by = 'revisor-fallas',
              resolution_notes = '${NOTES_ESCAPED}'
        WHERE id = '${REPORT_ID}';"
fi

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" postgres_db \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -P pager=off -c "$SQL"

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" postgres_db \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -x -P pager=off -c \
  "SELECT id, resolved, resolved_at, resolved_by, resolution_notes
     FROM error_reports WHERE id = '${REPORT_ID}';"
