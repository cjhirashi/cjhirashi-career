#!/usr/bin/env bash
# =============================================================================
#  .harness/gate/check.sh — compuerta del arnés SDD Anchored (simplificado)
#  Ver .harness/method.md §6.
#
#  Uso (desde la raíz del repo):
#    .harness/gate/check.sh            Verificación rápida (obligatoria al arrancar y al cerrar tarea).
#    .harness/gate/check.sh --full     Rápida + suites completas de los subproyectos con cambios.
#    .harness/gate/check.sh --help
#
#  Salida:  0 = compuerta abierta   ·   1 = algún ❌, compuerta cerrada (DETENERSE).
# =============================================================================
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"
H=".harness"

if [ -t 1 ]; then
  RED=$'\033[0;31m'; GRN=$'\033[0;32m'; YLW=$'\033[1;33m'; BLU=$'\033[0;34m'; BLD=$'\033[1m'; NC=$'\033[0m'
else RED=""; GRN=""; YLW=""; BLU=""; BLD=""; NC=""; fi

ERRORS=0; WARNS=0; PASSES=0
ok()   { echo "  ${GRN}✅${NC} $1"; PASSES=$((PASSES+1)); }
warn() { echo "  ${YLW}⚠️ ${NC} $1"; WARNS=$((WARNS+1)); }
err()  { echo "  ${RED}❌${NC} $1"; ERRORS=$((ERRORS+1)); }
skip() { echo "  ${BLU}⏭️ ${NC} $1"; }
sec()  { echo; echo "${BLD}$1${NC}"; }

MODE="fast"
case "${1:-}" in
  --full) MODE="full" ;;
  --help|-h) sed -n '3,13p' "$0" | sed 's/^#\{0,1\} \{0,1\}//'; exit 0 ;;
  "" ) ;;
  * ) echo "Opción desconocida: $1"; exit 2 ;;
esac

echo "${BLD}🔍 Arnés — compuerta (${MODE})${NC}"

# --- utilidades de front-matter (spec.md) -----------------------------------
fm_value() {  # $1=archivo  $2=clave  →  valor escalar del front-matter
  awk -v k="$2" '
    /^---[[:space:]]*$/ { n++; next }
    n==1 && $0 ~ "^"k":" { sub("^"k":[[:space:]]*",""); sub(/[[:space:]]*#.*$/,""); gsub(/["'\''[:space:]]/,""); print; exit }
  ' "$1"
}
fm_list() {  # $1=archivo  $2=clave de lista  →  ítems (uno por línea)
  awk -v k="$2" '
    /^---[[:space:]]*$/ { n++; next }
    n!=1 { next }
    $0 ~ "^"k":[[:space:]]*$" { inlist=1; next }
    inlist && /^[[:space:]]*-[[:space:]]/ { sub(/^[[:space:]]*-[[:space:]]*/,""); gsub(/["'\'']/,""); print; next }
    inlist && /^[^[:space:]-]/ { inlist=0 }
  ' "$1"
}

# =============================================================================
sec "1· Integridad"
for f in "$H/constitution.md" "$H/method.md" "$H/gate/check.sh" "$H/memory/state.md"; do
  [ -f "$f" ] && ok "$f" || err "falta $f"
done
[ -d "$H/specs" ] && ok "$H/specs/" || err "falta $H/specs/"
for t in git python3 node; do
  command -v "$t" >/dev/null 2>&1 && ok "$t $($t --version 2>&1 | head -1)" || warn "no está: $t"
done
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  ok "git — rama $(git rev-parse --abbrev-ref HEAD)"
else err "no es repo git"; fi

# =============================================================================
sec "2· Trazabilidad (specs implemented/verified)"
SPECS=$(find "$H/specs" -mindepth 2 -maxdepth 2 -name spec.md 2>/dev/null | grep -v '/_' | sort)
if [ -z "$SPECS" ]; then
  skip "sin specs todavía"
else
  while IFS= read -r sp; do
    d="$(dirname "$sp")"; name="$(basename "$d")"
    st="$(fm_value "$sp" estado)"
    case "$st" in
      implemented|verified) ;;
      *) ok "$name ($st) — no exige trazabilidad aún"; continue ;;
    esac
    tk="$d/tasks.md"
    [ -f "$tk" ] || { err "$name en $st sin tasks.md"; continue; }
    # nº de RF en la spec  vs  filas RF- en la tabla de cobertura de tasks.md
    rf_spec=$(grep -oE '\*\*RF-[0-9]+\*\*|RF-[0-9]+' "$sp" | grep -oE 'RF-[0-9]+' | sort -u | wc -l | tr -d ' ')
    rf_cov=$(grep -oE '\| *RF-[0-9]+' "$tk" | grep -oE 'RF-[0-9]+' | sort -u | wc -l | tr -d ' ')
    pend=$(grep -E '^\| *RF-[0-9]+' "$tk" | grep -Eiv '\| *(Pass|hecho) *\|? *$' | grep -c . || true)
    if [ "$rf_spec" -gt 0 ] && [ "$rf_cov" -lt "$rf_spec" ]; then
      err "$name: $rf_cov/$rf_spec RF en la tabla de cobertura de tasks.md"
    elif [ "$pend" -gt 0 ]; then
      err "$name: $pend fila(s) de cobertura sin 'Pass'/'hecho'"
    else
      ok "$name: cobertura completa ($rf_cov RF, 0 pendientes)"
    fi
  done <<< "$SPECS"
fi

# =============================================================================
sec "3· Anclaje (drift), documentación y regla de raíz"
if [ -z "$SPECS" ]; then
  skip "sin specs — nada que anclar"
else
  while IFS= read -r sp; do
    d="$(dirname "$sp")"; name="$(basename "$d")"
    ac="$(fm_value "$sp" anchor_commit)"; am="$(fm_value "$sp" anchor_mode)"; am="${am:-advisory}"
    mapfile -t COV < <(fm_list "$sp" covers)
    [ -n "$ac" ] || { warn "$name: sin anchor_commit en el front-matter"; continue; }
    [ "${#COV[@]}" -gt 0 ] || { warn "$name: sin covers[]"; continue; }
    git cat-file -e "${ac}^{commit}" 2>/dev/null || { warn "$name: anchor_commit '$ac' no existe (¿rebase?) — re-anchora"; continue; }
    spec_touched="$(git diff --name-only "$ac" -- "$d" 2>/dev/null | head -1)"
    changed="$(git diff --name-only "$ac" -- "${COV[@]}" 2>/dev/null)"
    if [ -z "$changed" ]; then ok "$name ($am): sin cambios en covers desde $ac"
    elif [ -n "$spec_touched" ]; then ok "$name ($am): covers y spec cambiaron — ok (mover anchor_commit al cerrar)"
    else
      n=$(echo "$changed" | grep -c .)
      msg="$name: DRIFT — $n archivo(s) de covers cambiaron desde $ac sin tocar la spec → re-anchor (method.md §9)"
      [ "$am" = "strict" ] && err "$msg" || warn "$msg"
    fi
  done <<< "$SPECS"
fi
# regla de raíz: TODO/FIXME sin ticket en el diff de trabajo
DIFF_ADD="$(git diff -U0 2>/dev/null | grep -E '^\+' | grep -Ei 'TODO|FIXME' | grep -Ev 'RF-[0-9]+|RNF-[0-9]+|ADR-[0-9]+' || true)"
if [ -n "$DIFF_ADD" ]; then err "TODO/FIXME sin ticket (RF-/RNF-/ADR-) en los cambios — Art. 10 (solución de raíz)"; echo "$DIFF_ADD" | sed 's/^/      /' | head -6
else ok "sin TODO/FIXME sin ticket en los cambios"; fi
# documentación: heurística — si el diff toca superficie observable, avisa
SURF="$(git diff --name-only 2>/dev/null | grep -E 'routes/|/api/|openapi|docker-compose|caddy.json|\.env' || true)"
DOCS_TOUCHED="$(git diff --name-only 2>/dev/null | grep -E '^docs/|README' || true)"
if [ -n "$SURF" ] && [ -z "$DOCS_TOUCHED" ]; then
  warn "el diff toca superficie observable (rutas/openapi/compose/caddy/env) y ningún doc del mapa — revisa Art. 11"
else ok "documentación: sin señal de obsolescencia"; fi

# =============================================================================
sec "4· Presupuesto de contexto"
budget() { [ -f "$1" ] || return 0; n=$(wc -l < "$1" | tr -d ' ');
  [ "$n" -le "$2" ] && ok "$1 · $n líneas (≤$2)" || warn "$1 · $n líneas (>$2) — consolida"; }
budget "$H/memory/state.md" 200
budget "$H/memory/history.md" 600
budget "$H/method.md" 400
[ -f AGENTS.md ] && budget AGENTS.md 200

# =============================================================================
sec "5· Bloques por perfil de arquitectura"
CHANGED="$(git diff --name-only 2>/dev/null; git diff --name-only --cached 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null)"
touched() { echo "$CHANGED" | grep -q "^$1/"; }

run_py_tests() {  # $1 = servicio
  local p="$1" py=""
  for v in venv_test venv venv_run; do [ -x "$p/$v/bin/python" ] && "$p/$v/bin/python" -c "import pytest" 2>/dev/null && { py="$p/$v/bin/python"; break; }; done
  if [ -z "$py" ]; then skip "$p · pytest no instalado en su venv — SKIP (instala deps de test para validar)"; return; fi
  echo "  ${BLU}→${NC} $p · pytest"
  if ( cd "$p" && "${py#$p/}" -m pytest -q -o addopts='' -p no:cacheprovider ) >/tmp/gate_$$.log 2>&1; then ok "$p · tests"
  else err "$p · tests FALLAN"; sed 's/^/      /' /tmp/gate_$$.log | tail -25; fi
  rm -f /tmp/gate_$$.log
}
run_node_tests() {  # $1 = subproyecto
  local p="$1"
  [ -d "$p/node_modules" ] || { skip "$p · sin node_modules — SKIP (npm ci)"; return; }
  echo "  ${BLU}→${NC} $p · type-check + vitest"
  if ( cd "$p" && npm run --silent type-check ) >/tmp/gate_$$.log 2>&1; then ok "$p · type-check"
  else err "$p · type-check FALLA"; sed 's/^/      /' /tmp/gate_$$.log | tail -20; fi
  if ( cd "$p" && npx --yes vitest run --reporter=dot ) >/tmp/gate_$$.log 2>&1; then ok "$p · vitest"
  else err "$p · vitest FALLA"; sed 's/^/      /' /tmp/gate_$$.log | tail -25; fi
  rm -f /tmp/gate_$$.log
}

for s in cjhirashi-career-api cjhirashi-career-ai; do
  if [ "$MODE" = "full" ] || touched "$s"; then run_py_tests "$s"; else skip "$s · sin cambios — SKIP"; fi
done
for s in cjhirashi-career-admin cjhirashi-career-portfolio; do
  if [ "$MODE" = "full" ] || touched "$s"; then run_node_tests "$s"; else skip "$s · sin cambios — SKIP"; fi
done
# contrato REST (activo cuando exista el openapi.yaml committeado)
OAS="cjhirashi-career-api/openapi.yaml"
if [ -f "$OAS" ]; then
  if command -v spectral >/dev/null 2>&1; then
    spectral lint "$OAS" >/tmp/gate_$$.log 2>&1 && ok "spectral: $OAS pasa el lint" || { err "spectral: $OAS falla"; sed 's/^/      /' /tmp/gate_$$.log | tail -12; }
    rm -f /tmp/gate_$$.log
  else warn "spectral no instalado — lint de contrato omitido"; fi
else skip "cjhirashi-career-api/openapi.yaml no existe — contrato REST aún no anclado"; fi
# MCP: validación de JSON Schema de tools tocadas
if echo "$CHANGED" | grep -q "cjhirashi-career-mcp/" ; then
  if find cjhirashi-career-mcp -name 'tools*.json' -o -name '*schema*.json' 2>/dev/null | grep -q .; then
    if command -v python3 >/dev/null 2>&1; then ok "mcp: (recordatorio) valida el JSON Schema de las tools tocadas"; fi
  fi
fi

# =============================================================================
sec "Resumen"
echo "  ${GRN}$PASSES ok${NC} · ${YLW}$WARNS warn${NC} · ${RED}$ERRORS error${NC}"
if [ "$ERRORS" -gt 0 ]; then
  echo; echo "${RED}${BLD}⛔ COMPUERTA CERRADA.${NC} Corrige los ❌ y re-ejecuta. No se marca nada 'verified'."
  exit 1
fi
echo; echo "${GRN}${BLD}✅ Compuerta abierta.${NC}"
[ "$WARNS" -gt 0 ] && echo "   ($WARNS aviso(s) — revísalos si tu tarea los toca.)"
exit 0
