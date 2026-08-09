# GuideU — Agile / Scrum Delivery Board

Delivery followed five two-week sprints. The repository keeps the long-lived
branches `main` and `sprint-1` through `sprint-5`; all five sprint branches are
complete and merged into `main`. Individual plan and review files remain the
authoritative record of planned versus delivered scope.

## Sprint 1 — Repository foundation ✅

- [x] Monorepo structure, repository hygiene and shared contracts
- [x] Django, FastAPI and Node/Socket.IO service foundations
- [x] Flutter and Next.js application scaffolds
- [x] Docker Compose, Nginx, MLflow and service CI workflows
- [x] Architecture, data, ethics, API and developer documentation

## Sprint 2 — Tourist discovery ✅

- [x] Email/password JWT authentication and secure mobile token handling
- [x] Mobile home, profile and navigation shell
- [x] Dataset-backed destination browsing and search
- [x] Verified-guide listing, search and guide profiles
- [x] Core-engine and mobile integration verification

## Sprint 3 — Marketplace transactions ✅

- [x] Tour-package browsing and package-centric booking flow
- [x] User-scoped bookings and payments
- [x] Demo eSewa/Khalti payment confirmation flow
- [x] Guide and route ratings/reviews with moderation state
- [x] Mobile booking, payment and review experiences

Real gateway signature and webhook verification remains explicitly outside the
thesis scope; the implemented confirmation action supports the documented demo
flow without representing itself as gateway-grade verification.

## Sprint 4 — AI and connectivity ✅

- [x] Route and guide recommendation feeds with graceful fallbacks
- [x] Anti-scam fair-price checks and overcharge reporting
- [x] Festival calendar and information hub
- [x] JWT-authenticated live chat with PostgreSQL message history
- [x] Read-only Next.js dashboard for overview, models, festivals and reports

PostgreSQL chat storage is an intentional architecture decision. Admin login,
moderation write actions and wider operations pages remain future work.

## Sprint 5 — Final product and deployment ✅

- [x] Travel workspaces, itineraries, budgets and AI suggestions
- [x] Currency conversion with cached live rates and static fallback
- [x] App-based SOS alert creation and resolution
- [x] Shared mobile loading, empty and retry states
- [x] Rate limiting, text sanitization, caching and query optimization
- [x] End-to-end backend journey tests and service quality gates
- [x] Production Compose, containerized web admin, Nginx and deployment guide
- [x] Thesis checklist, demo script and synchronized sprint documentation

Offline maps, on-device translation, real transport/accommodation inventory and
physical SOS hardware are documented future extensions rather than incomplete
sprint stories.

## Definition of Done

Delivered code is wired to its real API surface, checked by the relevant build
or test command, documented honestly, and committed to the applicable sprint
branch before being merged into `main`.
