# GuideU — Sprint Status (through Sprint 5 — complete)

GuideU is an AI-powered tourism platform for Nepal (BSc thesis + startup).
GitHub: `SubhamAdhikari20/guideu`.

## Architecture
Polyglot microservices monorepo (kebab-case service dirs):
- `services/core-engine` — Django + DRF + Celery + SimpleJWT (`config/` + `src/<app>`)
- `services/analytics-engine` — FastAPI ML (scam, recommendations, pricing, registry)
- `services/real-time-engine` — Node + TypeScript + Socket.IO
- `apps/mobile_app` — Flutter + Riverpod (clean architecture from `leelame`)
- `apps/web_admin` — Next.js 16 (admin dashboard)
- `shared/ infra/ data/ scripts/ docs/` (docker-compose + nginx + mlflow)

Databases: PostgreSQL, MongoDB, Redis.

Mobile clean architecture: `features/<f>/{data,domain,presentation}`. The data
layer returns `(Failure?, T?)` records (no Either). Riverpod for DI; list state
exposed as `AsyncValue`. Dio client attaches JWT and does a one-shot refresh on 401.

## Branches
`main` + `sprint-1`..`sprint-5`. All five sprint branches are complete and
merged into `main`. Local safety branch
`backup/pre-sprint1-2026-06-29` is preserved.

## Sprint 1 — DONE (merged)
Repository foundation: monorepo layout, service skeletons, infra
(docker-compose + nginx + mlflow), per-service CI, docs.

## Sprint 2 — DONE (merged)
Mobile frontend wired to the existing backend: auth (JWT, secure storage),
destinations (Explore), guides (list + profile), home + bottom-nav shell.

## Sprint 3 — DONE (merged)
Marketplace transaction layer: tour packages + bookings, payments
(eSewa/Khalti sheet → confirm), reviews/ratings shown on the guide profile.
Bookings are package-centric.

## Sprint 4 — DONE (merged)
The AI + connectivity sprint. Verify-and-fill-gaps: reused the existing ML
service, anti-scam tool, festival data and socket server; filled small backend
gaps and built the app frontends.
- **Backend gaps:** `recommendations` app (route + guide feed proxying the
  analytics-engine with DB enrichment + fallback); `chat` app (Postgres thread +
  message history, participant-scoped) with the real-time-engine persisting each
  delivered message; `catalog/events/upcoming/` festival calendar grouping.
- **Mobile:** "Recommended for you" on Home, anti-scam "Is this price fair?"
  screen + overcharge reporting, a Festivals tab (calendar/info hub), and live
  guide ↔ tourist chat (Socket.IO + REST history, opened from a booking).
- **Web admin:** first real dashboard (Overview, ML Models, Festivals, Scam
  Reports) with server-side fetches so secrets stay server-side.
- See `docs/sprints/sprint_4/` for the plan and review.

## Sprint 5 — DONE (merged)
Final sprint: features, polish, hardening, testing, deployment, docs.
- **Backend:** `workspace` (trips + items, reorder, budget, AI suggestions),
  `currency` (rates + convert, Celery refresh), `safety` (SOS alerts).
- **Mobile:** travel workspace screens (drag-and-drop itinerary + budget bar),
  currency converter + reusable price display, Emergency SOS, shared
  empty/error state widgets.
- **Hardening:** login/register rate limits, input sanitisation, Nginx security
  headers (`docs/architecture/SECURITY.md`); caching + query optimisation
  (`docs/performance/PERFORMANCE.md`).
- **Testing:** end-to-end journey test + per-app tests (21 backend tests pass).
- **Deploy/docs:** `docker-compose.prod.yml` + `scripts/deploy.sh` +
  `docs/DEPLOYMENT.md`; `docs/THESIS_SUBMISSION_CHECKLIST.md`, `docs/DEMO_SCRIPT.md`.
- See `docs/sprints/sprint_5/` for the plan and review.

## Data & ML phase (after sprint 5, distributed across the sprint branches)
The thesis's core requirement is using the Travel Planning dataset to build and
evaluate models. That work landed across all five sprint branches and is merged
into `main`:

- **sprint-1** — arrivals/gamification data loaders; ranking, regression and
  forecast metrics in `evaluation/metrics.py`.
- **sprint-2** — anti-scam classifier retrained with gradient boosting
  (accuracy 0.991, F1 0.980, Brier 0.006, cold-cell F1 0.958); **below-fair-wage
  flag** protecting guides and porters, enforced in both services.
- **sprint-3** — `guide_ranker`: predicts the rating a specific tourist gives a
  specific guide (RMSE 0.655 vs 0.688 for the mean; beats ranking by star rating).
- **sprint-4** — `route_recommender` rebuilt as a **learned** pointwise ranker
  (1.63× the popularity baseline on hit-rate@10, 1.38× as deployed with the
  diversity cap); recommendations now return the reasons behind each suggestion.
- **sprint-5** — `arrivals_forecaster` (MAPE 17.2% vs 38.6% seasonal naive) and
  `tourist_segments` (reported honestly: silhouette 0.13, no natural clusters);
  admin demand-forecast page; the research documentation.

**Five models, all ten dataset tables used, twelve baselines reported.** See
`docs/ml.md` (technical), `docs/MODELS_SIMPLE_OVERVIEW.md` (plain English) and
`docs/RESEARCH_FINDINGS.md` (the thesis evidence base). Retrain everything with
`python -m training.run_all --report artifacts/training_report.json`.

## Verification
`manage.py check` clean; core-engine `pytest` **26 passing**; analytics-engine
`pytest` **14 passing**; `flutter analyze`/`test` clean; Android debug APK build
clean; real-time-engine `tsc`/lint clean; web_admin lint/build clean.

## Key API endpoints (core-engine, `/api/v1`)
- `auth/token/`, `auth/token/refresh/`, `auth/register/`, `auth/users/me/`
- `catalog/{routes,regions,guides-registry,events,pricing-benchmarks}/`
  (+ `events/upcoming/`, `pricing-benchmarks/lookup/`)
- `bookings/{packages,bookings,itinerary-items}/`
- `payments/{payments,escrow}/` + `payments/{id}/confirm/`
- `reviews/reviews/` + `reviews/reviews/summary/`
- `recommendations/{routes,guides,forecast}/`
- `chat/{threads,messages}/`
- `trust/price-check/` + `trust/scam-reports/`
- `workspace/{trips,items}/` (+ `trips/{id}/{ai-suggestions,apply-suggestions,budget-summary}/`)
- `currency/{rates,convert}/`
- `safety/sos/` (+ `sos/{id}/resolve/`)

Pagination: page-number `{count, next, previous, results}`, page_size 25.

## Next (post-thesis / future work)
Offline map tile pre-download (needs route lat/lng), on-device chat translation,
real hotel/flight/bus inventory APIs, physical IoT SOS device, admin moderation
write actions + guide-verification / user-management pages.
