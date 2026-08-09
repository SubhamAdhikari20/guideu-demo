# GuideU — Demo Script (viva walkthrough)

A 10–12 minute path through the product that shows every headline feature. Run
the stack first: `docker compose up -d`, then `seed_from_dataset`. Launch the
Flutter app pointed at the gateway.

## 0. Setup (before the demo)
- Backend up; catalog seeded (routes, guides, festivals, price benchmarks).
- One tourist account + one approved guide; one tour package with a booking.

## 1. Onboarding (Sprint 2)
- Splash → Sign up / log in. Show JWT session persists on restart.

## 2. Discover (Sprint 2 + 4)
- Home: greeting, **"Recommended for you"** trek strip (ML feed), quick actions.
- Explore destinations; open a route detail sheet.
- Guides tab: search, open a guide profile with reviews.

## 3. Book & pay (Sprint 3)
- Open a tour package → book (pick dates) → pay with eSewa/Khalti sheet →
  booking moves to Confirmed.
- My Bookings: show the booking, then **Message** the guide.

## 4. Real-time chat (Sprint 4)
- In the chat room, send a message; show it persists (reopen → history loads).
- Mention live delivery is Socket.IO; history is stored server-side.

## 5. Anti-scam (Sprint 4)
- Home → "Is this price fair?" → enter a guide rate for a region → show the
  explainable verdict (fair / overpriced) and the report-overcharge action.

## 6. Festivals info hub (Sprint 4)
- Festivals tab → month-by-month calendar of Nepal festivals.

## 7. Plan a trip — the workspace (Sprint 5)
- Home → "Plan your trip" → New trip (title, dates, budget).
- Open the trip → **Suggest trip** (AI itinerary from the recommender) →
  items appear by day; **drag to reorder**; add a custom item; watch the
  **budget bar** update (green → red when over budget).

## 8. Currency + safety (Sprint 5)
- Profile → Currency Converter: convert NPR → USD; "show prices in USD".
- Profile → **Emergency SOS**: raise an alert (explain it's app + device ready).

## 9. Admin (Sprint 4 + 5)
- Open the Next.js admin: Overview counts, **ML Models** registry, Festivals,
  Scam Reports.

## 10. Engineering story (for the panel)
- Polyglot microservices: Django, FastAPI (ML), Node (realtime), Flutter, Next.js.
- AI: hybrid recommender + price-anomaly anti-scam, served from the ML service,
  surfaced through Django with graceful fallback.
- Quality: 21 backend tests incl. an end-to-end journey, security hardening,
  caching, and a production Docker Compose. See `docs/` for the details.
