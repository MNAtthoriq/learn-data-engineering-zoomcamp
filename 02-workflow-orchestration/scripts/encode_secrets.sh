#!/usr/bin/env bash
# converts .env.secrets (SECRET_KEY=plainValue) into .env_encoded (SECRET_KEY=base64Value) for Kestra's Secret requirement
# special case for GCP_CREDS_BASE64 since it already bas64Value from Terraform Output
# usage = ./scripts/encode_secrets.sh (it can run from anywhere so you may change as you need)

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

SRC=".env.secrets"
OUT=".env_encoded"

if [ ! -f "$SRC" ]; then
  echo "Missing $SRC." >&2
  echo "Copy .env.secrets.example to .env.secrets and fill in your values first." >&2
  exit 1
fi

: > "$OUT"
count=0

while IFS='=' read -r key value || [ -n "$key" ]; do
  # skip blank lines and comments
  case "$key" in
    ""|\#*) continue ;;
  esac

  # skip keys with no value set (left blank in .env.secrets)
  if [ -z "${value:-}" ]; then
    echo "Skipping $key (no value set)" >&2
    continue
  fi

  if [ "$key" = "GCP_CREDS_BASE64" ]; then
    echo "SECRET_GCP_CREDS=${value}" >>"$OUT"
  else
    encoded=$(printf '%s' "$value" | base64 | tr -d '\n')
    echo "SECRET_${key}=${encoded}" >>"$OUT"
  fi
  count=$((count + 1))
done <"$SRC"

echo "Wrote $count secret(s) to $OUT"
