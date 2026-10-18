#!/usr/bin/env bash
# Verifica que los compose declarados en COMPOSES cumplen el contrato de Coolify
# (sección "Contrato común" del plan ./superpowers/minimax/coolify/plan.md).
# Falla con "servicio: motivo" ante cualquier violación detectada.

set -euo pipefail

BASE_DIR="${BASE_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JQ_DIR="${SCRIPT_DIR}/coolify-check.d"

COMPOSES_DEFAULT=(
  "${BASE_DIR}|compose.supabase.yaml"
)

# Extrae del archivo compose todas las variables de la forma
# ${VAR}, ${VAR:-default}, ${VAR:?mensaje} o $VAR (simple).
extract_vars() {
  grep -oE '\$\{[A-Z_][A-Z0-9_]*(:[?][^}]*)?(-[^}]*)?\}|\$[A-Z_][A-Z0-9_]*' "$1" \
    | sed -E 's/^\$\{?([A-Z_][A-Z0-9_]*).*/\1/' \
    | sort -u
}

# Determina violaciones de "name" declaradas explícitamente en el YAML fuente
# (docker compose también añade "name" inferido del directorio en el JSON
# renderizado, así que validar ahí daría falsos positivos).
yaml_name_violations() {
  local compose_path="$1"
  python3 "${JQ_DIR}/yaml-names.py" "$compose_path"
}

run() {
  local compose_path="$1"
  local project_dir
  project_dir="$(dirname "$compose_path")"

  local env_file
  env_file="$(mktemp -t coolify-check.XXXXXX)"
  trap 'rm -f "${env_file:-}" "${violations_file:-}" "${stderr_path:-}"' EXIT

  local vars
  vars="$(extract_vars "$compose_path")"
  while IFS= read -r var; do
    [[ -z "$var" ]] && continue
    local fake_value
    if [[ "$var" =~ (URL|HOST|ORIGIN|ENDPOINT|EMAIL) ]]; then
      fake_value="https://ejemplo.invalid"
    else
      fake_value="x1234567890abcdef"
    fi
    printf '%s=%s\n' "$var" "$fake_value" >> "$env_file"
  done <<< "$vars"

  local stderr_path
  stderr_path="$(mktemp -t coolify-check.XXXXXX)"
  local rendered
  if ! rendered="$(docker compose --project-directory "$project_dir" -f "$compose_path" --env-file "$env_file" config --format json 2> "$stderr_path")"; then
    echo "FAIL: $compose_path no se pudo renderizar" >&2
    cat "$stderr_path" >&2
    rm -f "$env_file" "$stderr_path"
    exit 1
  fi
  rm -f "$stderr_path"

  local violations_file
  violations_file="$(mktemp -t coolify-check.XXXXXX)"
  printf '%s\n' "$rendered" > "$violations_file"

  local service_violations
  service_violations="$(jq -r -f "${JQ_DIR}/services.jq" < "$violations_file" || true)"

  local name_violations
  name_violations="$(yaml_name_violations "$compose_path")"

  local combined
  combined="$(
    {
      printf '%s\n' "$service_violations"
      printf '%s\n' "$name_violations"
    } | sed '/^$/d'
  )"

  rm -f "$violations_file"

  if [[ -n "$combined" ]]; then
    echo "Violaciones del contrato en $compose_path:" >&2
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      echo "  - $line" >&2
    done <<< "$combined"
    rm -f "$env_file"
    exit 1
  fi

  rm -f "$env_file"
  echo "OK: $compose_path cumple el contrato"
}

main() {
  local target="${1:-}"
  if [[ -n "$target" ]]; then
    run "$target"
    return
  fi
  for pair in "${COMPOSES_DEFAULT[@]}"; do
    local dir="${pair%%|*}"
    local file="${pair##*|}"
    run "$dir/$file"
  done
}

main "$@"
