# Sprint 4 — Review

Sprint 4 made GuideU genuinely AI-powered and connected: a personalised
recommendation feed, the anti-scam fair-price tool surfaced in the app, a
festival information hub, and real-time guide ↔ tourist chat — plus the first
real admin dashboard. As planned, this was mostly **wiring the app to backend
that already existed**, with small backend gap-fills. No ML models or the socket
server were rebuilt.

## What already existed (reused, not rebuilt)
- analytics-engine ML: scam scoring, route recommendations, guide ranking, price
  benchmarking and a model registry — all behind `X-API-Key`.
- core-engine: the ML client (`common/services.py`), the `trust` anti-scam tool
  (`/trust/price-check/`, `/trust/scam-reports/`), festivals (`catalog/events/`)
  and event ingestion (`analytics/events/`).
- real-time-engine: JWT-authed Socket.IO with presence and room-scoped chat.

## Backend gap-fills (small, additive)
1. **Recommendation feed** — new `recommendations` app:
   `GET /recommendations/routes/` and `/guides/`. Builds a tourist profile from
   the request, calls the analytics-engine, re-hydrates the ranked ids with real
   catalog rows, and falls back to top-rated / most-rewarding ordering when the
   ML service is down. (3 tests)
2. **Chat history** — new `chat` app (`ChatThread` + `ChatMessage` in Postgres)
   with `GET/POST /chat/messages/` and `GET /chat/threads/`. A `booking:<id>`
   room resolves both participants from the booking, and only participants can
   read or post. The real-time-engine now persists each delivered message by
   POSTing to this endpoint as the sending user (best-effort, never blocks live
   delivery). (3 tests)
3. **Festival info hub** — `GET /catalog/events/upcoming/` groups festivals by
   month (de-duplicated across years, regions aggregated) for the calendar. (1 test)

Decision: chat history lives in **Postgres**, not MongoDB. It keeps the feature
inside the proven, tested stack; MongoDB is noted as a later optimisation.

## Mobile (Flutter, clean architecture)
- **Recommendations** — a "Recommended for you" trek strip on Home, reusing the
  existing `Destination` entity (the feed returns the same catalog JSON).
- **Anti-scam** — an "Is this price fair?" screen (service / price / region /
  season), an explainable verdict, and one-tap overcharge reporting.
- **Festivals** — a new "Festivals" tab: the year's festival calendar grouped by
  month with type, duration, regions and badge points.
- **Live chat** — a Socket.IO client (`socket_io_client`), an inbox of threads,
  and a conversation screen that loads REST history then streams live messages.
  Reachable from a booking ("Message") and the Home chat icon.

Each feature follows `data / domain / presentation`, returns `(Failure?, T?)`
from the data layer, and exposes state as a Riverpod `AsyncValue`.

## Web admin (Next.js 16, App Router)
A first real dashboard with a sidebar shell and four pages: Overview (counts),
ML Models (the analytics-engine registry), Festivals (the calendar) and Scam
Reports. Protected/secret reads happen in server components, so the ML key and
admin token never reach the browser.

## Verification
- core-engine: `manage.py check` clean; `pytest` — **7 passed** (recommendations,
  chat, festivals). Added a test-only `conftest.py` (in-memory cache) so tests
  run without Redis.
- real-time-engine: `npm run build` (tsc) clean.
- mobile: `flutter analyze` clean; `flutter test` passing.
- web_admin: `npm run lint` and `npm run build` clean.

## Deferred / next
- Full admin **auth + write actions** (verify/dismiss reports, edit events) — the
  dashboard reads now; moderation actions need the admin login flow.
- MongoDB-backed chat (currently Postgres).
- Running the MLflow training sweeps as a documented experiment (models/artifacts
  already ship in the analytics-engine).
- Carried-over guide-verification + user-management admin pages.
