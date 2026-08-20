# Running the demo under Docker

`docs/setup/DEVELOPMENT.md` covers the native run (each service in its own venv).
This page covers the Docker path and, specifically, the gap between "the stack is
up" and "the stack can be demonstrated".

## The short version

```bash
# Docker Desktop must be running first.
cd guideu
./scripts/demo_setup_docker.sh
```

The script is idempotent — re-run it any time. It brings the stack up, seeds the
catalog, creates the tourist/guide/admin demo logins, verifies protected API
access and checks that the administrator login is reachable. It exits non-zero
when a service or protected workflow is unavailable.

When it finishes:

| What               | Where                                                             | Credentials                                |
| ------------------ | ----------------------------------------------------------------- | ------------------------------------------ |
| Admin dashboard    | [http://localhost:3000](http://localhost:3000)                     | `admin@guideu.local` / `AdminDemo123!` |
| API docs (Swagger) | [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/) | —                                         |
| Analytics engine   | [http://localhost:8001/health](http://localhost:8001/health)       | header`X-API-Key`                        |
| MLflow             | [http://localhost:5000](http://localhost:5000)                     | —                                         |

The dashboard header should read **Services 3/3**.

## Demo accounts

Created by `--with-demo-accounts`. Re-seeding always resets these passwords, so
a re-run before a demo restores known credentials rather than preserving drift.

| Email                    | Password            | Role    | What it has                                            |
| ------------------------ | ------------------- | ------- | ------------------------------------------------------ |
| `tourist@guideu.local` | `TouristDemo123!` | TOURIST | 3 confirmed bookings, 1 chat thread with the guide     |
| `guide@guideu.local`   | `GuideDemo123!`   | GUIDE   | verified, guide profile, assigned to the demo bookings |
| `admin@guideu.local`   | `AdminDemo123!`   | ADMIN   | staff + superuser; dashboard and moderation            |

`demo_tourist_0..9@example.com` also exist with `TouristDemo123!` — they own the
remaining demo bookings.

### Tourist and guide portals

The Flutter app chooses its shell from the authenticated role. Tourist sign-up
creates a tourist account; guide sign-up also collects a licence number and bio,
then waits for administrator verification before the guide can accept work.

The tourist **Guides** directory still uses `GuideRegistry` records from
`verified_guides.csv` for discovery. The on-demand marketplace uses real GUIDE
user accounts instead: tourists publish a request, verified available guides
send price/ETA offers, and the tourist accepts one offer before payment and chat.

Sign in as `guide@guideu.local` to open the dedicated guide shell. It includes
verification and availability state, nearby requests, offer creation/update,
assignments, trip progression, chat, earnings/escrow, ratings, profile settings
and logout. The seeded account is verified and available, and the seed includes
two open nearby requests so the offer workflow can be demonstrated immediately.

### Seeded demo users could not log in (fixed)

`_seed_demo_bookings` created its tourists with `get_or_create`, which never
hashes a password — so they were created with an **empty password hash**. They
existed, owned bookings and appeared in the admin, but every login attempt
returned 400. The only way to find this is to try it.

The seeder now sets a password on every demo user it touches, on every run.
Guarded by `src/catalog/test_demo_accounts.py`.

## Running the mobile app against Docker

The Flutter app runs on the host, not in a container.

**Android emulator** — works with no changes. `api_endpoints.dart` defaults to
`http://10.0.2.2:8000/api/v1`, which is how the emulator reaches the host
loopback, and Docker publishes 8000/8001/8002 there.

**Real device over USB** — the device has its own loopback, so forward the ports
first, then relaunch the app (a hot reload will not pick up a new base URL):

```bash
adb reverse tcp:8000 tcp:8000
adb reverse tcp:8001 tcp:8001
adb reverse tcp:8002 tcp:8002
```

`adb.exe` lives in `%LOCALAPPDATA%\Android\Sdk\platform-tools\`, not on PATH,
and the forwards do not survive a USB replug.

**Real device over Wi-Fi** — point the app at the laptop's LAN address instead:

```bash
flutter run \
  --dart-define=GUIDEU_API_BASE_URL=http://192.168.1.81:8000/api/v1 \
  --dart-define=GUIDEU_REALTIME_URL=http://192.168.1.81:8002
```

### `DisallowedHost` blocked the emulator (fixed)

`.env` and `docker-compose.yml` pin `DJANGO_ALLOWED_HOSTS` to
`localhost,127.0.0.1,core-engine`. The emulator's requests arrive with
`Host: 10.0.2.2:8000`, and a Wi-Fi device's with the laptop's LAN IP — neither
is in that list, so Django answered **400 DisallowedHost** to every request
including login. In the app that surfaces as a generic "no internet connection",
which points nowhere near the cause.

`config/settings/dev.py` now sets `ALLOWED_HOSTS = ["*"]`, alongside the
`CORS_ALLOW_ALL_ORIGINS` that is already there for the same reason. Development
only: `prod.py` imports from `base.py`, not from `dev.py`, and the production
compose pins `config.settings.prod`.

### Suggested tourist run-through

Sign in as `tourist@guideu.local` / `TouristDemo123!`:

1. **Home** — recommendations strip (served by the ML recommender), Plan-trip and
   Safety CTAs.
2. **Explore** — 2,000 dataset-backed routes; open one for the detail sheet.
3. **Find a guide** — create a request and compare its fair-price benchmark and
   guide offers; use the guide account on a second device to send an offer.
4. **Hotels / Flights / Buses** — filter seeded local inventory, reserve seats
   or rooms, pay in demo/sandbox mode, and inspect My Travel Bookings.
5. **My Bookings** — open a confirmed package booking and its itinerary.
6. **Message** on a booking — live chat over Socket.IO; the thread already has an
   opening exchange with Pemba, so it is obviously working before you type.
7. **Price check** (anti-scam) — quote 25,000 NPR for a Guide in Everest/Khumbu
   and watch it come back as a likely scam against the benchmark.
8. **Profile** — notifications, trip workspace, settings, security, currency and
   Emergency SOS.

### Suggested guide run-through

Sign in as `guide@guideu.local` / `GuideDemo123!`, confirm availability is on,
open **Nearby requests**, send a price and ETA offer, and accept it from the
tourist device. The assignment then moves through en-route, arrived, active and
completed states, with chat throughout. Completion releases the escrow entry
into guide earnings and enables the tourist's post-trip rating.

Registering live works too: Sign up takes Full Name, Email, Phone and a password
of at least 8 characters; choosing Guide additionally requires the licence
fields. Registration is throttled to 5/min and login to 10/min, so do not retry
in a tight loop on stage.

## Why `docker compose up` on its own is not enough

`up` gives you a *migrated but empty* Postgres. That produces empty screens that
look like bugs but are setup gaps:

| Symptom                                     | Cause                                                   | Fix                                               |
| ------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------- |
| Festivals: "No festivals found"             | Postgres is empty; the compose volume is fresh          | `seed_from_dataset`                             |
| Admin pages redirect to login                | Administrator session is required                      | sign in with the seeded administrator         |
| Demand forecast: "Train the arrivals model" | see below — this one*was* a real bug                 | fixed                                             |

The script seeds the data and checks protected API access. The administrator UI
uses HttpOnly login cookies, so the browser must sign in rather than receiving a
long-lived token from `.env`.

## The forecast bug (fixed)

This one deserves recording because the symptom pointed away from the cause.

Under Docker the **Model registry page listed all five models** while the
**Demand forecast page said the model was not trained**. Both read the same
service, so one of them had to be lying.

`artifacts/model_registry.json` is written at training time and recorded an
**absolute path from the training machine**:

```json
"artifact_path": "C:\\Users\\...\\analytics-engine\\artifacts\\arrivals_forecaster.joblib"
```

The registry travels with the artifacts into the image and the `ml_artifacts`
volume; that Windows path does not exist inside a Linux container. So:

- `list_models()` reads the JSON only → the registry page rendered all five.
- `load_model()` checked `Path(card.artifact_path).exists()` → `False` → `None`
  → every inference path degraded to an empty result.

The `.joblib` files were sitting in `/app/artifacts` the whole time. Only the
recorded path was unusable.

**The fix**, in `services/analytics-engine/registry.py`:

- `save_model` now records just the filename, so new registries are portable.
- `_resolve_artifact` resolves a card against the *current* `artifact_dir` and
  still accepts the old absolute paths, so existing registries keep working.
- `load_model` logs a warning when nothing resolves, instead of silently
  returning `None`.
- `/health` now reports `models_loadable` and `unavailable`, so "registered" and
  "actually loadable" can no longer disagree without saying so.

Covered by `tests/test_registry_paths.py`.

### The general lesson

This is the same shape as the defects in `docs/DEFECTS_AND_FIXES.md`: a
**wiring** problem, not a logic one, hidden by a graceful fallback. Every ML
endpoint is written to degrade quietly when a model is missing, which is right
for production and terrible for diagnosis — the dashboard showed five healthy
models while nothing could score. Hence the `/health` change: the gap between
what is registered and what can load is now reported rather than inferred.

## A stale cache can also empty the calendar

`/catalog/events/upcoming/` caches for 30 minutes. If the page was opened
**before** seeding, the empty answer was cached, and seeding then appeared to do
nothing for half an hour — during a demo, that reads as a broken feature.

`upcoming` now refuses to cache an empty calendar (`src/catalog/views.py`), so it
self-heals on the next request. Regression test in `src/catalog/tests.py`.

If you hit a stale cache from an older run:

```bash
docker compose exec core-engine python -c "
import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.dev')
django.setup()
from django.core.cache import cache; cache.clear(); print('cleared')"
```

## Administrator sessions expire

The dashboard stores access and refresh tokens in HttpOnly cookies after a
successful administrator login. The access token lasts 12 hours and the refresh
token lasts 7 days by default. If the header reports an expired administrator
session, sign in again at `/login`; the demo setup script does not write browser
credentials or bearer tokens into `.env`.

## Useful commands

```bash
docker compose ps                       # what is running
docker compose logs -f core-engine      # tail a service
docker compose restart web-admin        # after changing .env

# The dashboard image is a production build with no bind mount, so UI changes
# need a rebuild; core-engine and analytics-engine are bind-mounted and reload.
docker compose up -d --build web-admin
```

Seeding is idempotent, so re-running it is always safe:

```bash
docker compose exec core-engine python manage.py seed_from_dataset \
  --with-demo-accounts --with-demo-bookings --with-demo-scam-reports
```

`--with-demo-scam-reports` imports ~40 rows from `scam_reports.csv` spread across
severity bands and left in `SUBMITTED`, which is the only state in which the
verify/dismiss actions are enabled. Without it the moderation queue is empty and
the trust-and-safety workflow cannot be shown at all.
