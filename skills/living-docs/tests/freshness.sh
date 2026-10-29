#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="$(git -C "$skill_dir/../../../" rev-parse --show-toplevel)"
freshness="$skill_dir/scripts/freshness.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/docs"
source_sha="$(git -C "$repo_root" hash-object README.md)"

printf '%s\n' \
  '---' \
  'knowledge:' \
  '  - observed' \
  'sources:' \
  "  - \"README.md | $source_sha | lines 1-5\"" \
  '---' \
  '# Readable source metadata' > "$tmp/docs/readable.md"

printf '%s\n' \
  '---' \
  'knowledge:' \
  '  - observed' \
  'sources:' \
  '  - path: README.md' \
  "    sha: $source_sha" \
  '    lines: 1-5' \
  '---' \
  '# Legacy source metadata' > "$tmp/docs/legacy.md"

output="$(cd "$repo_root" && bash "$freshness" --wiki-root "$tmp/docs" 2>&1)" || {
  printf '%s\n' "$output" >&2
  exit 1
}

case "$output" in
  *"Observed pages : 2"*"Up to date     : 2"*"Sources checked: 2"*) ;;
  *)
    printf 'Unexpected freshness output:\n%s\n' "$output" >&2
    exit 1
    ;;
esac

printf '%s\n' 'PASS: readable and legacy source metadata are both checked.'
