#!/usr/bin/env bash
# Build and (re)start the GuideU production stack.
# Usage: ./scripts/deploy.sh
set -euo pipefail

COMPOSE="docker compose -f docker-compose.prod.yml"

echo "==> Checking required environment (.env)"
test -f .env || { echo "Missing .env — copy .env.example and fill it in."; exit 1; }

echo "==> Building images"
$COMPOSE build

echo "==> Starting services (migrations + collectstatic run on boot)"
$COMPOSE up -d

echo "==> Current status"
$COMPOSE ps

echo "Done. Logs: $COMPOSE logs -f core-engine"
