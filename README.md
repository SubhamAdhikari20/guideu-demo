# GuideU — All-in-One AI Tourism Platform for Nepal

> Verified guides, fair pricing, anti-scam intelligence and end-to-end trip
> planning — delivered as a production-grade, polyglot microservices monorepo.

GuideU helps tourists in Nepal book **verified guides**, plan trips, and avoid
**scams/over-pricing**, while giving vendors reach and authorities trustworthy
oversight. It is both a final-year thesis project and an intended startup, built
to professional engineering standards.

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
| **3** | Tour packages, bookings, demo payment confirmation and reviews | ✅ done |
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
