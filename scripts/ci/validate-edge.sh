#!/usr/bin/env bash
# Validate Caddy edge configs used in production deployment.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

CADDY_IMAGE="${CADDY_IMAGE:-caddy:2-alpine}"

validate() {
  local file="$1"
  echo "Validating $file"
  docker run --rm \
    -v "$ROOT/$file:/etc/caddy/Caddyfile:ro" \
    -e EDGE_DOMAIN=app.example.com \
    -e ACME_EMAIL=ops@example.com \
    "$CADDY_IMAGE" \
    caddy validate --config /etc/caddy/Caddyfile
}

validate infrastructure/edge/Caddyfile
validate infrastructure/edge/Caddyfile.internal

echo "Edge Caddy configs OK"
