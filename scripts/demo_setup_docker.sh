#!/usr/bin/env bash
# Bring the GuideU stack up under Docker and leave it in a demonstrable state.
#
# `docker compose up` alone is NOT enough for a demo. It gives you a migrated but
# empty Postgres, which is why data-backed screens and moderation queues are
# empty. The dashboard itself now uses an HttpOnly administrator login session.
# This script closes that gap and is safe to re-run.
#
# Usage: ./scripts/demo_setup_docker.sh
set -euo pipefail

cd "$(dirname "$0")/.."

ADMIN_EMAIL="admin@guideu.local"
ADMIN_PASSWORD="AdminDemo123!"

echo "==> Checking prerequisites"
docker version >/dev/null 2>&1 || { echo "Docker daemon is not running. Start Docker Desktop first."; exit 1; }
test -f .env || { echo "Missing .env — copy .env.example to .env first."; exit 1; }
test -d "../Travel Planning" || { echo "Missing '../Travel Planning' dataset next to the repo."; exit 1; }

echo "==> Building and starting the stack"
docker compose up -d --build

echo "==> Waiting for core-engine and analytics-engine"
for i in $(seq 1 60); do
  core=$(curl -fsS -o /dev/null -w '%{http_code}' http://localhost:8000/healthz/ 2>/dev/null || echo 000)
  ml=$(curl -fsS -o /dev/null -w '%{http_code}' http://localhost:8001/health 2>/dev/null || echo 000)
  [ "$core" = "200" ] && [ "$ml" = "200" ] && break
  sleep 3
  [ "$i" = "60" ] && { echo "Services did not come up. Try: docker compose logs core-engine analytics-engine"; exit 1; }
done
echo "    core-engine and analytics-engine are up"

echo "==> Seeding the catalog (idempotent; ~1 minute on a cold database)"
docker compose exec -T core-engine python manage.py seed_from_dataset \
  --with-demo-accounts --with-demo-bookings --with-demo-scam-reports

# The admin/tourist/guide logins are created by --with-demo-accounts above.

echo "==> Verifying administrator authentication"
PAIR=$(curl -fsS -X POST http://localhost:8000/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")
TOKEN=$(printf '%s' "$PAIR" | python -c 'import json,sys; print(json.load(sys.stdin)["access"])')
test -n "$TOKEN" || { echo "Could not obtain a token."; exit 1; }

echo "==> Verifying protected APIs and the administrator login"
fail=0
for endpoint in \
  auth/users/ \
  bookings/guide-requests/ \
  bookings/travel-offerings/ \
  trust/scam-reports/ \
  safety/sos/; do
  if curl -fsS -o /dev/null \
    -H "Authorization: Bearer ${TOKEN}" \
    "http://localhost:8000/api/v1/${endpoint}?page_size=1"; then
    printf '    %-34s ok\n' "/api/v1/${endpoint}"
  else
    printf '    %-34s FAILED\n' "/api/v1/${endpoint}"
    fail=1
  fi
done
if curl -fsS -o /dev/null http://localhost:3000/login; then
  printf '    %-34s ok\n' "/login"
else
  printf '    %-34s FAILED\n' "/login"
  fail=1
fi

echo
if [ "$fail" = "0" ]; then
  echo "Ready."
  echo
  echo "  Admin dashboard  http://localhost:3000/login  (sign in; header should read Services 3/3)"
  echo "  API docs         http://localhost:8000/api/docs/"
  echo "  MLflow           http://localhost:5000"
  echo
  echo "  Demo logins (mobile app and dashboard):"
  echo "    tourist@guideu.local   TouristDemo123!   TOURIST  - 3 bookings, 1 chat thread"
  echo "    guide@guideu.local     GuideDemo123!     GUIDE    - verified portal + nearby requests"
  echo "    ${ADMIN_EMAIL}   ${ADMIN_PASSWORD}     ADMIN    - dashboard + moderation"
  echo
  echo "  Android emulator: the app's default 10.0.2.2:8000 works as-is."
  echo "  Real device over USB: adb reverse tcp:8000 tcp:8000 (also 8001, 8002)."
else
  echo "A required service or protected endpoint failed — see docs/setup/DOCKER_DEMO.md."
  exit 1
fi
