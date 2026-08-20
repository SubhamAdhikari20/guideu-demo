# GuideU — System Architecture

GuideU is a polyglot, microservices-oriented platform for tourism in Nepal. It
solves four problems the proposal identifies — **overpricing/scams**,
**fragmented planning**, **unreliable guide trust**, and **lack of
personalization** — by splitting responsibilities across services that each use
the database and runtime best suited to their workload.

## Service map

| Service | Stack | Port | Datastore | Responsibility |
|---|---|---|---|---|
| `core-engine` | Django 6 + DRF, Python 3.12 | 8000 | PostgreSQL | Authoritative business logic: accounts/RBAC, catalog, bookings, payments/escrow, permits, reviews, favorites, notifications, analytics ingest, audit. Publishes domain events to Redis. |
| `analytics-engine` | FastAPI, scikit-learn, pandas, (PyTorch/MLflow optional) | 8001 | MongoDB + artifacts | ML inference and training: anti-scam scoring, recommendations, guide ranking, price benchmarking. Reads the synthetic dataset for training. |
| `real-time-engine` | Node.js + Express + TypeScript + Socket.IO | 8002 | Redis (pub/sub) | Low-latency transport: chat, live booking/permit/payment status, guide availability, presence. Subscribes to Django's Redis events and fans them out over WebSockets. |
| `web-admin` | Next.js (in `apps/`, host-run) | 3000 | — | Operator/admin dashboard and moderation. |
| `mobile-app` | Flutter (in `apps/`, host-run) | — | — | Tourist + guide apps. |

> **Naming note.** This repo's committed README uses `analytics-engine` and
> `real-time-engine`; the project brief alternately calls these `ml-service` and
> `realtime-engine`. We keep the committed names to stay consistent with the
> architecture diagram already in `README.md`. See
> [DECISIONS.md](DECISIONS.md#adr-0001).

## How a request flows

```
Flutter / Next.js
   │  REST (JWT)                         WebSocket (Socket.IO, JWT handshake)
   ▼                                                  ▲
core-engine (Django/DRF) ──HTTP──► analytics-engine (FastAPI)   │
   │  post_save signals                  ▲  batch pulls          │
   ▼                                     │                       │
 Redis  ── pub: guideu:*.events ─────────┴───── sub ────► real-time-engine
   ▲
PostgreSQL (ACID core)        MongoDB (flexible ML/event docs)
```

1. A client calls the Django REST API (e.g. confirm a booking).
2. Django commits to PostgreSQL inside a transaction.
3. A `post_save` signal publishes a compact event to a Redis channel
   (`guideu:booking.events`, `guideu:payment.events`, `guideu:permit.events`,
   `guideu:user.events`).
4. `real-time-engine` is subscribed to those channels and pushes the update into
   the relevant Socket.IO rooms (`tourist:<id>`, `guide:<id>`, `booking:<id>`,
   and the administrator-only `role:ADMIN` room).
5. For decisions that need ML (is this price a scam? what to recommend?), Django
   or the client calls `analytics-engine` over HTTP; the ML service serves a
   versioned model artifact.

This is the event contract the existing Django signals already emit — the
realtime service is built to that contract rather than inventing a new one.

## Database polyglot strategy

- **PostgreSQL** — every sensitive, relational, transactional entity (users,
  bookings, payments, escrow ledger, permits, reviews, audit). ACID guarantees
  protect money and identity.
- **MongoDB** — the analytics-engine's flexible documents: feature logs, model
  metadata, scoring/inference request logs, and denormalised recommendation
  payloads whose shape evolves with the models.
- **Redis** — cross-service pub/sub broker, DRF cache backend, Celery broker, and
  ephemeral presence/availability state for the realtime engine.

## Cross-cutting concerns

- **Auth** — JWT (SimpleJWT). The realtime engine verifies the same HS256 token
  on the socket handshake using a shared secret.
- **Versioning** — REST is mounted under `/api/v1/`. ML models are versioned via
  artifact directories + an MLflow-style registry (`model_registry.json`).
- **Security/ethics** — least-privilege object permissions, throttling, audit
  logging, no hardcoded secrets, fairness auditing on ML outputs (the dataset
  intentionally encodes a nationality price-bias the scam model must not learn to
  reproduce as discrimination). See [ethics-and-fairness.md](ethics-and-fairness.md).

See [data.md](data.md) for how the synthetic dataset maps onto these services,
and [api-contracts.md](api-contracts.md) for the cross-service interfaces.
