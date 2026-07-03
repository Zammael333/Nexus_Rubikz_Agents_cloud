#!/usr/bin/env bash
# Paso 114 — Rotación automática de secretos
# Uso: GITHUB_TOKEN=xxx ./scripts/rotate_secrets.sh <env> <key> <value>
set -euo pipefail

ENV="${1:-dev}"
KEY="${2:-}"
VALUE="${3:-}"

if [ -z "$KEY" ] || [ -z "$VALUE" ]; then
  echo "Uso: GITHUB_TOKEN=xxx $0 <env> <key> <value>"
  echo "Ej:   GITHUB_TOKEN=ghp_xxx $0 prod GCP_SERVICE_ACCOUNT_JSON '\${{ secrets.GCP_SA_PROD }}'"
  exit 1
fi

REPO="anomalyco/nexus-rubykz"

if ! command -v gh &>/dev/null; then
  echo "gh CLI required. Install: https://cli.github.com/"
  exit 1
fi

echo "Setting secret $KEY for $ENV..."
echo "$VALUE" | gh secret set "${ENV}_${KEY}" --repo "$REPO"
echo "Done."
