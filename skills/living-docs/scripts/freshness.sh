#!/usr/bin/env bash
# Living Docs deterministic freshness checker.
#
# A documentation page with knowledge: observed should normally cite source files in
# YAML frontmatter. Each source entry stores the git blob hash of the inspected content.
# If the current file hash differs, the page is "stale" (needs review).
#
# Usage:
#   freshness.sh [--wiki-root docs] [--json] [--stale-only]
#
# No external YAML parser is required. Readable source entries use:
#   "path | full-git-blob-hash | lines 1-20"
# The earlier path/sha mapping form is still accepted.

set -euo pipefail

WIKI_ROOT="docs"
MODE="text"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --wiki-root)
      WIKI_ROOT="${2:-}"
      shift 2
      ;;
    --json)
      MODE="json"
      shift
      ;;
    --stale-only)
      MODE="stale"
      shift
      ;;
    -h|--help)
      sed -n '1,18p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "freshness.sh must run inside a Git repository" >&2
  exit 2
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

if [ ! -d "$WIKI_ROOT" ]; then
  echo "Documentation root not found: $WIKI_ROOT" >&2
  exit 2
fi

stale_pages=()
ungrounded_pages=()
ok_pages=0
observed_pages=0
checked_sources=0

json_escape() {
  python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null || \
    sed 's/\\/\\\\/g; s/"/\\"/g' | awk '{printf "\"%s\\n\"", $0}'
}

while IFS= read -r -d '' page; do
  fm=$(awk '/^---[[:space:]]*$/{c++; next} c==1{print} c>=2{exit}' "$page")
  [ -n "$fm" ] || continue

  # Detect observed in either inline form: knowledge: [intent, observed]
  # or block form:
  # knowledge:
  #   - intent
  #   - observed
  if ! printf '%s\n' "$fm" | awk '
      BEGIN { in_k=0; found=0 }
      /^knowledge:[[:space:]]*/ {
        line=$0
        if (line ~ /observed/) found=1
        in_k=1
        next
      }
      in_k && /^[^[:space:]]/ { in_k=0 }
      in_k && /^[[:space:]]*-[[:space:]]*observed([[:space:]]|$)/ { found=1 }
      END { exit found ? 0 : 1 }
    '; then
    continue
  fi

  observed_pages=$((observed_pages + 1))

  entries=()
  while IFS= read -r line; do
    [ -n "$line" ] && entries+=("$line")
  done < <(
    printf '%s\n' "$fm" | awk '
      function trim(value) {
        sub(/^[[:space:]]+/, "", value)
        sub(/[[:space:]]+$/, "", value)
        return value
      }
      function unquote(value) {
        if ((substr(value, 1, 1) == "\"" && substr(value, length(value), 1) == "\"") ||
            (substr(value, 1, 1) == "\047" && substr(value, length(value), 1) == "\047"))
          return substr(value, 2, length(value) - 2)
        return value
      }
      function flush_legacy() {
        if (path != "") print path "\t" sha
        path=""
        sha=""
      }
      /^sources:[[:space:]]*$/ { in_sources=1; next }
      in_sources && /^[^[:space:]]/ { flush_legacy(); in_sources=0 }
      in_sources && /^[[:space:]]*-[[:space:]]*path:[[:space:]]*/ {
        flush_legacy()
        path=$0
        sub(/^[[:space:]]*-[[:space:]]*path:[[:space:]]*/, "", path)
        path=unquote(trim(path))
        sha=""
        next
      }
      in_sources && /^[[:space:]]*-[[:space:]]*/ {
        flush_legacy()
        value=$0
        sub(/^[[:space:]]*-[[:space:]]*/, "", value)
        value=unquote(trim(value))
        count=split(value, parts, "[|]")
        source_path=trim(parts[1])
        source_sha=(count >= 2 ? trim(parts[2]) : "")
        if (source_path != "") print source_path "\t" source_sha
        next
      }
      in_sources && /^[[:space:]]+sha:[[:space:]]*/ {
        sha=$0
        sub(/^[[:space:]]+sha:[[:space:]]*/, "", sha)
      }
      END { flush_legacy() }
    '
  )

  if [ "${#entries[@]}" -eq 0 ]; then
    ungrounded_pages+=("$page")
    continue
  fi

  page_stale=0
  reasons=()

  for entry in "${entries[@]}"; do
    path=${entry%%$'\t'*}
    recorded_sha=${entry#*$'\t'}
    path=$(printf '%s' "$path" | sed -e 's/^['"'"']//' -e 's/['"'"']$//')
    recorded_sha=$(printf '%s' "$recorded_sha" | sed -e 's/^['"'"']//' -e 's/['"'"']$//')

    checked_sources=$((checked_sources + 1))

    if [ -z "$recorded_sha" ]; then
      page_stale=1
      reasons+=("$path: missing recorded sha")
      continue
    fi

    if [ ! -f "$path" ]; then
      page_stale=1
      reasons+=("$path: source missing")
      continue
    fi

    current_sha=$(git hash-object "$path")
    if [ "$current_sha" != "$recorded_sha" ]; then
      page_stale=1
      reasons+=("$path: content changed (${recorded_sha:0:8} -> ${current_sha:0:8})")
    fi
  done

  if [ "$page_stale" -eq 1 ]; then
    joined=$(printf '%s\n' "${reasons[@]}" | paste -sd ';' -)
    stale_pages+=("$page"$'\t'"$joined")
  else
    ok_pages=$((ok_pages + 1))
  fi

done < <(find "$WIKI_ROOT" -type f -name '*.md' -print0)

case "$MODE" in
  stale)
    for line in "${stale_pages[@]:-}"; do
      [ -n "$line" ] && printf '%s\n' "${line%%$'\t'*}"
    done
    ;;
  json)
    # Keep JSON generation dependency-free except for optional python escaping.
    printf '{\n'
    printf '  "observed_pages": %d,\n' "$observed_pages"
    printf '  "ok_pages": %d,\n' "$ok_pages"
    printf '  "checked_sources": %d,\n' "$checked_sources"
    printf '  "stale": ['
    first=1
    for line in "${stale_pages[@]:-}"; do
      [ -n "$line" ] || continue
      page=${line%%$'\t'*}
      reason=${line#*$'\t'}
      [ "$first" -eq 1 ] || printf ','
      printf '\n    {"page":"%s","reason":"%s"}' \
        "$(printf '%s' "$page" | sed 's/\\/\\\\/g; s/"/\\"/g')" \
        "$(printf '%s' "$reason" | sed 's/\\/\\\\/g; s/"/\\"/g')"
      first=0
    done
    [ "$first" -eq 1 ] || printf '\n  '
    printf '],\n'
    printf '  "ungrounded_observed": ['
    first=1
    for page in "${ungrounded_pages[@]:-}"; do
      [ -n "$page" ] || continue
      [ "$first" -eq 1 ] || printf ','
      printf '\n    "%s"' "$(printf '%s' "$page" | sed 's/\\/\\\\/g; s/"/\\"/g')"
      first=0
    done
    [ "$first" -eq 1 ] || printf '\n  '
    printf ']\n}\n'
    ;;
  text)
    echo "Living Docs freshness"
    echo "====================="
    echo "Observed pages : $observed_pages"
    echo "Up to date     : $ok_pages"
    echo "Stale          : ${#stale_pages[@]}"
    echo "Ungrounded     : ${#ungrounded_pages[@]}"
    echo "Sources checked: $checked_sources"
    echo

    if [ "${#stale_pages[@]}" -gt 0 ]; then
      echo "Potentially stale pages:"
      for line in "${stale_pages[@]}"; do
        page=${line%%$'\t'*}
        reason=${line#*$'\t'}
        echo "  - $page"
        echo "    $reason"
      done
      echo
    fi

    if [ "${#ungrounded_pages[@]}" -gt 0 ]; then
      echo "Observed pages without sources[]:"
      for page in "${ungrounded_pages[@]}"; do
        echo "  - $page"
      done
      echo
    fi

    if [ "${#stale_pages[@]}" -eq 0 ] && [ "${#ungrounded_pages[@]}" -eq 0 ]; then
      echo "No deterministic freshness issues found."
    fi
    ;;
esac

# Nonzero means findings exist, useful in CI. --stale-only intentionally also
# returns nonzero when findings exist so callers can choose `|| true` if desired.
if [ "${#stale_pages[@]}" -gt 0 ] || [ "${#ungrounded_pages[@]}" -gt 0 ]; then
  exit 1
fi
