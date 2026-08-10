# Cross-Service Contracts

The three backend services integrate through three stable contracts: REST,
Redis events, and Socket.IO events. Frontends depend only on REST + Socket.IO.

## 1. Redis event bus (core-engine ⇒ real-time-engine)

Django publishes compact JSON to these channels on `post_save`:

| Channel | Emitted by | Example payload |
|---|---|---|
| `guideu:user.events` | `authentication` | `{ "event": "user.created", "user_id": 12, "role": "GUIDE" }` |
| `guideu:booking.events` | `bookings` | `{ "event": "booking.status.confirmed", "booking_id": 7, "booking_reference": "AB12CD34EF90", "status": "CONFIRMED", "tourist_id": 3, "assigned_guide_id": 9, "timestamp": "..." }` |
| `guideu:payment.events` | `payments` | `{ "event": "payment.status.success", "payment_id": 4, "user_id": 3, "booking_id": 7, "amount": "180.00", "gateway": "KHALTI", "timestamp": "..." }` |
| `guideu:permit.events` | `permits` | `{ "event": "permit.status.verified", "permit_id": 2, "applicant_id": 3, "permit_type": "TIMS", "status": "VERIFIED", "timestamp": "..." }` |
| `guideu:notification.events` | `notifications` | `{ "event": "notification.created", "user_id": 3, "notification_id": 88, "kind": "BOOKING", "title": "...", "body": "..." }` |

Every payload carries an `event` discriminator of the form
`<domain>.<verb>[.<status>]`. The realtime engine routes by domain + the ids in
the payload.

## 2. Socket.IO events (real-time-engine ⇔ clients)

Handshake: `io(url, { auth: { token: "<JWT access token>" } })`. The token is the
same SimpleJWT access token Django issues; the engine verifies it with the shared
HS256 secret and joins the socket to its identity rooms.

| Direction | Event | Payload |
|---|---|---|
| server→client | `booking:update` | mirror of `guideu:booking.events` |
| server→client | `payment:update` | mirror of `guideu:payment.events` |
| server→client | `permit:update` | mirror of `guideu:permit.events` |
| server→client | `notification:new` | mirror of `guideu:notification.events` |
| client→server | `chat:join` | `{ "room": "booking:<booking id>" }` |
| client→server | `chat:message` | `{ "room": "booking:<booking id>", "body": "..." }` |
| server→client | `chat:message` | `{ "room", "from", "body", "ts" }` |
| client→server | `guide:availability` | `{ "available": true }` (verified guides only) |
| server→client | `presence:update` | `{ "user_id", "online": true }` |

Rooms: `user:<id>`, `tourist:<id>`, `guide:<id>`, `booking:<booking id>`.

Booking rooms use the booking's **primary key**, not its public reference. The
Flutter app joins `booking:${booking.id}` and the core-engine parses the room
back to an integer pk when it resolves participants, so anything fanning out on
the reference lands in a room with nobody in it.

## 3. ML inference REST (clients / core-engine ⇒ analytics-engine)

Base: `http://analytics-engine:8001`. Internal calls send
`X-API-Key: $ANALYTICS_API_KEY`. Interactive docs at `/docs`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | liveness + loaded model versions |
| `POST` | `/api/v1/scam/score` | overcharge/scam probability for a quote |
| `POST` | `/api/v1/recommendations/routes` | personalized route ranking for a tourist |
| `POST` | `/api/v1/guides/rank` | rank candidate guides for a request |
| `POST` | `/api/v1/pricing/benchmark` | fair-price range lookup for a service |
| `GET` | `/api/v1/models` | model registry (versions, metrics, trained-at) |

### `POST /api/v1/scam/score`
```jsonc
// request
{ "service_type": "Licensed Guide", "region": "Everest/Khumbu",
  "season": "Peak (Autumn)", "quoted_price_npr": 9000 }
// response
{ "scam_probability": 0.83, "is_likely_scam": true, "severity": "Severe Overcharge",
  "benchmark_price_npr": 4725, "overcharge_ratio": 1.90, "model_version": "scam-v1",
  "explanation": ["quoted is 1.9x the fair benchmark", "service+region peak premium applied"] }
```

### `POST /api/v1/recommendations/routes`
```jsonc
// request
{ "tourist": { "pref_adventure_score": 0.82, "pref_culture_score": 0.3,
  "pref_nature_score": 0.6, "budget_band": "Mid-range", "fitness_level": "Good" },
  "season": "Autumn", "top_k": 5 }
// response
{ "model_version": "rec-v1", "items": [
  { "route_id": "RTE0001", "route_name": "Everest Base Camp", "score": 0.91,
    "components": { "adventure_fit": 0.95, "season_fit": 1.0, "budget_fit": 0.7 } } ] }
```

All responses are versioned (`model_version`) and explainable (component scores /
explanation arrays) to satisfy the proposal's traceability requirement.
