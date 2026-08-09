# Sprint 4 — Plan

Sprint 4 is the AI sprint: **recommendations, anti-scam pricing, the festival
information hub, and real-time guide ↔ tourist chat**. As in Sprints 2 and 3,
most of the heavy backend already exists, so the work is mostly **wiring the
mobile app to it**, plus a few small backend gap-fills (no rebuilds).

## What already exists (verified)
- `analytics-engine` (FastAPI ML) already serves the models behind `X-API-Key`:
  - `POST /api/v1/scam/score` — explainable overcharge / scam probability
  - `POST /api/v1/recommendations/routes` — content-based + popularity route ranking
  - `POST /api/v1/guides/rank` — verified-guide ranking
  - `POST /api/v1/pricing/benchmark` and `GET /api/v1/models` (model registry)
  - Trained artifacts live in `services/analytics-engine/artifacts/`.
- core-engine already has the ML client `src/common/services.py`
  (`recommend_routes`, `rank_guides`, `score_scam`) with graceful fallback.
- core-engine `trust` app already exposes the anti-scam tool:
  `/api/v1/trust/price-check/` and `/api/v1/trust/scam-reports/`.
- core-engine `catalog` already exposes festivals (`/api/v1/catalog/events/`)
  and fair-price benchmarks (`/api/v1/catalog/pricing-benchmarks/lookup/`).
- `real-time-engine` (Socket.IO) already has JWT auth, presence and a
  room-scoped `chat:join` / `chat:message` flow for `booking:*` rooms.
- Dataset for training sits in `Travel Planning/` (`cultural_events.csv`,
  `verified_guides.csv`, `recommendation_interactions.csv`, ...).

So Sprint 4 does **not** rebuild the ML models or the socket server. It fills the
gaps that block the user-facing features.

## Backend gaps to fill (small, additive)
1. **Recommendation feed for tourists.** The ML client exists but nothing exposes
   it to the app. Add a `recommendations` app: `GET /recommendations/routes/` and
   `GET /recommendations/guides/` that build the tourist profile from the request,
   call the analytics-engine, enrich the results with real catalog rows, and fall
   back to top-rated / popular ordering when the ML service is down.
2. **Chat history.** The socket broadcasts live messages but nothing stores them.
   Add a `chat` app (Postgres `ChatThread` + `ChatMessage`) with REST endpoints to
   list threads, read history, and persist a message, so the app can show past
   messages and the socket handles live delivery. (MongoDB is noted as a later
   optimisation — Postgres keeps it inside the proven, tested stack for the thesis.)
3. **Festival info hub.** Add an `upcoming` action on the events endpoint that
   groups festivals by month for the calendar view.

## Mobile work (Flutter, clean architecture)
4. **Recommendations** — a "Recommended for you" section on Home (suggested
   routes + guides) from the new feed endpoints.
5. **Anti-scam** — a "Is this price fair?" check screen wired to
   `/trust/price-check/`, plus reporting an overcharge.
6. **Festival hub** — a festival calendar / information screen from
   `/catalog/events/upcoming/`.
7. **Live chat** — a chat screen using `socket_io_client` for live messages and
   the REST history endpoint for the backlog.

Each follows `data / domain / presentation`, returns `(Failure?, T?)` from the
data layer, and exposes list state as a Riverpod `AsyncValue`.

## Web admin (Next.js)
8. A first real dashboard: model registry view (from analytics-engine `/models`),
   festival/event management, and scam-report moderation — the carried-over admin
   work, kept lean.

## Commit sequence (plain messages, pushed after each)
1. start sprint 4 and add the plan
2. add recommendation feed endpoints for routes and guides
3. add chat message history with threads
4. add upcoming festivals endpoint for the info hub
5. add recommended for you section on the home screen
6. add fair price check and report a scam screen
7. add festival calendar and information hub screen
8. add live chat between tourists and guides
9. add admin dashboard for models, events and scam reports
10. write sprint 4 review notes

## Verification
`manage.py check`, the analytics-engine tests, `flutter analyze` / `flutter test`,
and `npm run build` (web admin) must pass before their respective commits.
