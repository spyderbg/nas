#!/usr/bin/env bash
# Manage the site relationship using rc aliases configured on this admin host.
# No credentials are read from the Compose environment or printed by this script.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./rustfs-site-replication.sh [status|link] [alias-a] [alias-b]

Defaults: status nas-a nas-b
Configure both aliases with the RustFS rc client before running this script.
Run link ONCE to establish whole-site replication. Inspect status after a
timeout or failure before retrying link; the request may already have applied.
EOF
}

if [[ ${1:-} == --help || ${1:-} == -h ]]; then
  usage
  exit 0
fi

action=${1:-status}
site_a=${2:-nas-a}
site_b=${3:-nas-b}
if (( $# > 3 )) || [[ $action != status && $action != link ]]; then
  usage >&2
  exit 2
fi
if [[ -z $site_a || -z $site_b || $site_a == -* || $site_b == -* || $site_a == "$site_b" ]]; then
  echo "Provide two distinct rc aliases that do not start with a dash." >&2
  exit 2
fi
if ! command -v rc >/dev/null 2>&1; then
  echo "Install the RustFS rc client first; see docs/rplicate.md." >&2
  exit 1
fi

for site in "$site_a" "$site_b"; do
  rc ready "$site"
done

if [[ $action == link ]]; then
  echo "Linking $site_a and $site_b for whole-site replication."
  if ! rc admin replicate add "$site_a" "$site_b"; then
    echo "Link request failed or timed out. Inspect both sites before retrying:" >&2
    echo "  $0 status $site_a $site_b" >&2
    exit 1
  fi
fi

for site in "$site_a" "$site_b"; do
  rc admin replicate info "$site"
  rc admin replicate status "$site"
done
