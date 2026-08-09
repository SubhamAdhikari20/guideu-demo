# Sprint 5 — Plan (final sprint)

Sprint 5 turns GuideU into a complete, demoable, thesis-ready product. It adds the
last features (travel workspace, currency, safety SOS), polishes the app, hardens
security, adds end-to-end tests, and ships a production deployment setup plus the
thesis documentation.

As in the earlier sprints, this follows the real repo (kebab-case services,
`leelame` clean architecture on mobile) and the verify-and-fill-gaps style — it
does **not** rebuild what already works (auth, catalog, bookings, payments,
reviews, recommendations, anti-scam, chat, festivals, the ML service, the admin
dashboard).

## Honest scope (expected in a thesis)

**Full implementation**
- Travel workspace + day-by-day itinerary builder with budget tracking
- AI itinerary suggestions (reuses the Sprint 4 recommendation feed)
- Currency conversion (NPR base, live rates with a static fallback)
- App-based safety SOS alerts (share location + alert contacts)
- UI polish: shared empty / error / loading (shimmer) states
- Security hardening: rate limiting, input sanitisation, security headers
- Performance: query optimisation + Redis caching on hot endpoints
- End-to-end backend tests for the real user journeys
- Production deployment config (compose + gunicorn + deploy script)
- Thesis documentation + demo script

**Scaffold / simulated (documented as such)**
- IoT SOS "wearable" → an in-app SOS button + alert record. No real hardware; the
  backend is ready for a device to POST to the same endpoint later.

**Out of scope (future work, documented honestly)**
- Offline GPS map tile pre-download — the catalog routes have no lat/lng yet, so a
  real map needs a data-model change; recorded as future work.
- On-device ML-Kit chat translation — heavy native dependency; the chat is built,
  translation is future work.
- Real hotel / flight / bus inventory APIs — third-party integrations, future work.

## Existing backend we build on (verified)
- core-engine apps: authentication, catalog, bookings, payments, reviews,
  favorites, notifications, analytics, recommendations, chat, trust, gamification,
  audit. `src/<app>` layout, `config.settings.dev`, page-number pagination.
- analytics-engine ML behind `X-API-Key`; the Django ML client lives in
  `common/services.py` (`recommend_routes`, `rank_guides`, `score_scam`).
- DRF uses URLPathVersioning, so APIView / @action handlers take `*args, **kwargs`.
- Tests use a `conftest.py` that swaps the Redis cache for in-memory.

## Commit sequence (plain messages, pushed after each)
1. start sprint 5, add the plan and thesis checklist
2. add travel workspace with day-by-day itinerary and budget
3. add ai itinerary suggestions to the workspace
4. add currency conversion with live rates and fallback
5. add safety sos alerts
6. add the travel workspace screens on the mobile app
7. add currency converter and price display and the sos button
8. polish the app with shared empty, error and loading states
9. add rate limiting and input cleaning for security
10. speed up the api with caching and add end to end tests
11. add production docker compose and a deploy script
12. write thesis docs, demo script and the sprint 5 review

## Verification (before each commit)
`manage.py check` + `pytest` (core-engine), `flutter analyze` / `flutter test`
(mobile), `tsc` build (realtime), `npm run lint` / `build` (web admin).
