#!/usr/bin/env bash
# Exporta un mes de analítica del portafolio (eventos, visitas y visitantes) a JSONL comprimido.
# Es una copia de respaldo: el crudo NUNCA se borra de la base (SPEC-0010, RF-020/RF-021).
#
# Uso:   export_portal_events.sh [AAAA-MM]        (por defecto, el mes anterior en America/Mexico_City)
# Salida: $OUT_DIR/AAAA-MM.jsonl.gz (eventos), AAAA-MM.visits.jsonl.gz, AAAA-MM.visitors.jsonl.gz
# Variables: PG_CONTAINER (postgres_db), PG_USER (career_admin), PG_DB (career_db),
#            OUT_DIR (/mnt/disco2/cjhirashi-data/backups/portal-analytics), TZ_NAME (America/Mexico_City)
set -euo pipefail

PG_CONTAINER="${PG_CONTAINER:-postgres_db}"
PG_USER="${PG_USER:-career_admin}"
PG_DB="${PG_DB:-career_db}"
OUT_DIR="${OUT_DIR:-/mnt/disco2/cjhirashi-data/backups/portal-analytics}"
TZ_NAME="${TZ_NAME:-America/Mexico_City}"

month="${1:-$(TZ="$TZ_NAME" date -d "$(TZ="$TZ_NAME" date +%Y-%m-01) -1 month" +%Y-%m)}"
[[ "$month" =~ ^[0-9]{4}-(0[1-9]|1[0-2])$ ]] || { echo "Mes inválido: $month (usa AAAA-MM)" >&2; exit 2; }
next="$(date -d "$month-01 +1 month" +%Y-%m)"

mkdir -p "$OUT_DIR"

export_table() {  # tabla, columna de tiempo, archivo
  local table="$1" column="$2" file="$3" tmp
  tmp="$(mktemp "$OUT_DIR/.tmp.XXXXXX")"
  docker exec -i "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -At -v ON_ERROR_STOP=1 -c \
    "COPY (SELECT row_to_json(t) FROM $table t
           WHERE $column >= timestamptz '$month-01 00:00 $TZ_NAME'
             AND $column <  timestamptz '$next-01 00:00 $TZ_NAME'
           ORDER BY $column, id) TO STDOUT" | gzip -9 > "$tmp"
  gzip -t "$tmp"
  mv "$tmp" "$OUT_DIR/$file"
  printf '%s: %s filas\n' "$file" "$(gzip -dc "$OUT_DIR/$file" | wc -l)"
}

export_table portal_events   created_at "$month.jsonl.gz"
export_table portal_visits   started_at "$month.visits.jsonl.gz"
export_table portal_visitors first_seen "$month.visitors.jsonl.gz"
