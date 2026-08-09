# Thesis Submission Checklist — GuideU

Module ST6000CEM (Coventry University / Softwarica College). This maps each thesis
deliverable to where it lives in the repo, so the report can cite real artefacts.

## 1. System design artefacts
- [ ] Context diagram — `Important_Images/Context Diagram - GuideU.png`
- [ ] Architecture overview — `README.md` + `docs/architecture/CLEAN_ARCHITECTURE.md`
- [ ] ER diagram — generate from the Django models (`core-engine/src/*/models.py`)
- [ ] Sequence diagrams (booking, payment, chat) — to draw from the flows in
      `bookings`, `payments`, `chat` apps
- [ ] Use-case diagram — roles in `authentication.models.User.Roles`

## 2. Implementation evidence
- [x] Monorepo with five services (Sprint 1) — `services/`, `apps/`
- [x] Auth + profiles + catalog (Sprint 2)
- [x] Bookings + payments + reviews (Sprint 3)
- [x] ML recommendations + anti-scam + chat + festivals (Sprint 4)
- [x] Workspace + currency + safety + polish + deploy (Sprint 5)
- [ ] Screenshots of every major screen — capture from the running mobile app
      (use the prototype set in `Important_Images/Prototype and Design/` as a guide)

## 3. AI / ML chapter
- [ ] Model approach write-up — `services/analytics-engine/README.md` +
      `docs/ml/` (recommenders, price benchmarking)
- [ ] Evaluation metrics + model registry — analytics-engine `/api/v1/models`,
      surfaced in the web admin "ML Models" page
- [ ] Synthetic vs real data note — dataset in `Travel Planning/`

## 4. Testing chapter
- [ ] Unit + integration test list — `services/core-engine/src/**/tests.py`,
      `services/core-engine/tests/` (e2e)
- [ ] Coverage report — `docs/testing/` (generated in Sprint 5)
- [ ] Mobile widget tests — `apps/mobile_app/test/`

## 5. Non-functional chapter
- [ ] Security measures — `docs/architecture/SECURITY.md`
- [ ] Performance / caching notes — `docs/performance/` (Sprint 5)
- [ ] Ethics & privacy — `docs/ethics-and-fairness.md`

## 6. Deployment / DevOps
- [ ] CI per service — `.github/workflows/`
- [ ] Production setup — `docker-compose.prod.yml` + `scripts/deploy.sh`
- [ ] Environment reference — `.env.example`

## 7. Project management
- [x] Sprint plans + reviews — `docs/sprints/sprint_1..5/`
- [x] Decision log — `docs/DECISIONS.md`
- [ ] Demo script — `docs/DEMO_SCRIPT.md` (Sprint 5)

## 8. Known limitations / future work (be honest)
- Offline map tile pre-download (needs route lat/lng)
- On-device chat translation
- Real hotel / flight / bus inventory integrations
- Physical IoT SOS device (the app SOS + backend endpoint are ready for it)
