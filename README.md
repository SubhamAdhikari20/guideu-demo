# GuideU — All-in-One AI Tourism Platform for Nepal

> Verified guides, fair pricing, anti-scam intelligence and end-to-end trip
> planning — delivered as a production-grade, polyglot microservices monorepo.

GuideU helps tourists in Nepal request and compare offers from **verified
guides**, book local travel services, plan trips, and avoid
**scams/over-pricing**. Guides have a dedicated availability, offer, assignment,
chat, and trip-progress portal; administrators have an authenticated operations
console. It is both a final-year thesis project and an intended startup.

---

## 🏛️ Architecture

A polyglot, fault-isolated microservices architecture behind an nginx gateway.

```text
        ┌─────────────────────────┐        ┌──────────────────────────┐
        │  Flutter mobile_app      │        │  Next.js web_admin        │
        │  (tourists & guides)     │        │  (admin / moderator)      │
        └───────────┬─────────────┘        └────────────┬─────────────┘
                    └──────────────┬──────────────────────┘
                          ┌────────▼─────────┐   nginx (API gateway)
                          └────────┬─────────┘
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                            ▼
┌────────────────┐        ┌────────────────┐          ┌────────────────────┐
│  core-engine   │        │ real-time-engine│         │  analytics-engine   │
│ Django + DRF   │        │ Node + Socket.IO│         │  FastAPI + sklearn  │
└──────┬─────────┘        └────────┬────────┘          └─────────┬──────────┘
       │ publishes events          │ subscribes                  │ inference
       └─────────────────►  ┌──────┴──────┐  ◄───────────────────┘
                            │    Redis     │
                            └──────┬───────┘
            ┌──────────────────────┴───────────────────────┐
            ▼                                               ▼
    ┌────────────────┐                            ┌────────────────┐
    │  PostgreSQL    │                            │    MongoDB     │
    └────────────────┘                            └────────────────┘
```

## 🧰 Tech stack

| Layer | Service | Technology |
| --- | --- | --- |
| Business API | `services/core-engine` | Django 6 + DRF + Celery + SimpleJWT |
| ML inference | `services/analytics-engine` | FastAPI + scikit-learn (+ optional PyTorch/MLflow) |
| Realtime | `services/real-time-engine` | Node.js + TypeScript + Socket.IO |
| Mobile | `apps/mobile_app` | Flutter + Riverpod (clean architecture) |
| Admin | `apps/web_admin` | Next.js + TypeScript + Tailwind |
| Data | — | PostgreSQL · MongoDB · Redis |
| Infra | `infra/` | Docker Compose · nginx · MLflow · GitHub Actions · uv |

## 📂 Repository layout

```text
guideu/
├── apps/
│   ├── mobile_app/     # Flutter (clean architecture + Riverpod)
│   └── web_admin/      # Next.js admin (App Router, layered)
├── services/
│   ├── core-engine/    # Django + DRF (config/ + src/<apps>)
│   ├── analytics-engine/ # FastAPI ML service
│   └── real-time-engine/ # Node + Socket.IO
├── shared/             # cross-service TS types & constants
├── infra/              # nginx gateway config
├── data/               # dataset workspace (git-ignored contents)
├── scripts/            # setup / lint / test helpers
├── docs/               # architecture, ADRs, data, ml, ethics, sprints
├── docker-compose.yml  # full local stack (+ override + mlflow + nginx)
└── Makefile            # developer task runner (make help)
```

## ⚡ Quick start

```bash
cp .env.example .env
./scripts/setup.sh            # uv sync + npm install + flutter pub get
docker compose up --build     # datastores, backend services, web admin, mlflow, nginx
```

Or run services individually with the Makefile (`make help`).

Seed a complete local demonstration with:

```bash
make seed-demo
```

With the Docker demo running, exercise the complete tourist, guide and
administrator journey through public HTTP endpoints with:

```bash
make acceptance
```

| Role | Email | Password |
| --- | --- | --- |
| Tourist | `tourist@guideu.local` | `TouristDemo123!` |
| Guide | `guide@guideu.local` | `GuideDemo123!` |
| Administrator | `admin@guideu.local` | `AdminDemo123!` |

These accounts exist only when the demo seeder is explicitly run.

## Delivered workflows

- Tourist: registration/login/reset, discovery, AI recommendations, on-demand
  guide requests and offer comparison, tour packages, hotel/flight/bus
  reservations, itinerary workspace, fair-price checks, payments, chat,
  notifications, settings, currency and SOS.
- Guide: licence-aware registration, administrator verification, availability,
  nearby requests, price/ETA offers, assignments, lifecycle updates and chat.
- Administrator: cookie-backed login, users, guide verification, all booking
  types, travel inventory, verified payments/escrow, reviews, scam reports, SOS,
  festivals, demand forecasts and the ML registry.

Payments are server-priced and support three explicit modes. `demo` is an
offline local simulation; `sandbox` uses provider-hosted eSewa/Khalti checkout
and server-side callback/lookup verification; `live` requires production
credentials and fails closed when they are absent. See `.env.example`.

### Running the services natively (without Docker)

Two things bite here and neither one announces itself, so they are written
down rather than rediscovered:

1. **Point the core engine at a local analytics engine.** `.env` ships
   `ANALYTICS_ENGINE_URL=http://analytics-engine:8001`, which is the
   docker-compose service name and only resolves inside compose. Run natively
   without overriding it and every ML call fails DNS, degrades quietly to a
   benchmark answer, and recommendations come back `"source": "fallback"` for
   the whole session.

   ```bash
   ANALYTICS_ENGINE_URL=http://localhost:8001 python manage.py runserver 8000 --noreload
   ```

2. **Wait for the analytics engine to warm up.** It loads five models on start
   and takes roughly 15 to 20 seconds. Calls made during that window hit the
   4 second client timeout and fall back silently, so an early request looks
   like a broken model rather than a cold one.

Check both at once before demoing anything:

```bash
curl -s http://localhost:8000/readyz/
# {"status": "ready", "ml_predictions": "live", ...}
```

If that says `degraded`, the response names which dependency is down and, for
the DNS case above, tells you which URL to use instead.

## 🌐 Service URLs (local)

| Service | URL |
| --- | --- |
| core-engine (Django) | http://localhost:8000 · admin `/admin/` · docs `/api/docs/` |
| analytics-engine (FastAPI) | http://localhost:8001/docs |
| real-time-engine (Socket.IO) | ws://localhost:8002 |
| web_admin (Next.js) | http://localhost:3000 |
| MLflow UI | http://localhost:5000 |
| nginx gateway | http://localhost:80 |

## 🗓️ Sprint roadmap

| Sprint | Scope | Status |
| --- | --- | --- |
| **1** | Repository foundation: monorepo, service skeletons, infra, CI, docs | ✅ done |
| **2** | Mobile authentication, discovery, destinations and guides | ✅ done |
| **3** | Tour packages, guide offers, travel services, verified payments and reviews | ✅ done |
| **4** | Recommendations, anti-scam, festivals, chat and admin dashboard | ✅ done |
| **5** | Travel workspace, currency, SOS, hardening, deployment and thesis polish | ✅ done |

All five sprint branches are complete and merged into `main`. Detailed plans
and delivery reviews live in [`docs/sprints/`](docs/sprints/). The full
architecture, ADRs, dataset mapping, ML and ethics rationale are in
[`docs/`](docs/).

## 🌿 Branching & commits

Long-lived branches only: `main`, `sprint-1` … `sprint-5` (no feature branches).
Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
(`type(scope): subject`).

## 📜 License

MIT — see [LICENSE](LICENSE).
