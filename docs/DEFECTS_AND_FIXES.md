# Defects Found and Fixed

A record of the bugs found when the system was run end-to-end against a real
database rather than only through its test suite. It is written up because the
*pattern* is the interesting part: every one of these passed CI, and several
were invisible precisely because the code around them degraded gracefully.

This is the evidence behind the thesis's testing section. The honest summary:
**the test suite was green while the flagship feature returned 500 on every
call**, and it stayed green because nothing exercised the running system.

---

## 1. Nothing was migrated, so the app could not serve at all

**Symptom.** `db.sqlite3` existed but was 0 bytes; no migration had been applied.

**Why it hid.** `pytest-django` builds a fresh test database for every run, so
34 tests passed against a schema the development database did not have.

**Fix.** `manage.py migrate` + `manage.py seed_from_dataset`. Documented in the
setup notes so a fresh clone reaches a working state.

---

## 2. Redis was a hard dependency of a "zero-setup" configuration

**Symptom.** Every cached endpoint returned **500 ConnectionError** without a
Redis server. `/api/v1/catalog/routes/` — the app's most basic read — was dead.

**Why it hid.** `conftest.py` swapped the cache for `LocMemCache` so tests would
be hermetic. That fix made the suite pass while the actual application stayed
broken, which is the worst combination.

**Root cause.** `dev.py` documents itself as booting "with no external
services", but inherited `base.py`'s Redis cache. Django's built-in `RedisCache`
has no ignore-errors mode, so a missing Redis is fatal rather than a cache miss.

**Fix.** `dev.py` falls back to `LocMemCache` unless `REDIS_URL` is set in the
environment. Both compose files set it explicitly, so containers and production
are unchanged and a bare `runserver` now works.

---

## 3. Fourteen API actions raised `TypeError` on every request

**Symptom.** `/auth/users/me/`, `/payments/{id}/confirm/`,
`/reviews/reviews/summary/`, `/trust/scam-reports/{id}/verify/` and ten others
returned 500:

```
TypeError: UserViewSet.me() got an unexpected keyword argument 'version'
```

**Root cause.** The API is mounted at `path("api/<version>/", ...)` for
`URLPathVersioning`, so Django passes `version="v1"` into every handler. Any
handler written as `def handler(self, request)` — with no `**kwargs` — rejects
it. Four handlers had `*args, **kwargs`; fourteen did not.

**Why it hid.** No test called any of them. The endpoints that *were* tested
happened to be the four written correctly.

**Fix.** `*args, **kwargs` on all fourteen, plus a contract test
(`tests/test_api_contract.py`) that walks the URL conf and inspects every
mounted handler's signature. A handler added later with the wrong shape now
fails immediately, naming itself.

The first version of that guard was itself wrong: it kept one route per view
class, so viewset `@action` routes — the broken ones — were never inspected. It
was verified by deliberately re-breaking a handler and confirming the test
caught it.

---

## 4. `/auth/users/me/` returned 403 to the user it exists for

**Root cause.** `UserViewSet.get_permissions()` mapped the CRUD actions and fell
through to `IsAdminUser()` for everything else, silently overriding the
`@action(permission_classes=[IsAuthenticated])` on `me`.

**Fix.** `get_permissions()` now defers to `super()` for any non-CRUD action, so
an action's own declaration wins. Covered by a parametrised test over the
self-service routes.

---

## 5. Every ML call was rejected, and the fallback hid it

**Symptom.** Recommendations, guide ranking and forecasting all silently served
their non-personalised fallback. The API returned 200 the whole time.

**Root cause.** `ANALYTICS_API_KEY` defaulted to `""` in the core-engine and
`"change-me-internal-service-token"` in the analytics-engine. With no `.env`,
the two never matched and the ML service answered 401.

**Why it hid.** The graceful-degradation path worked *too* well: the feed always
returned results, so nothing looked wrong from the outside. This is the failure
mode the whole thesis argument about ML value depends on not having.

**Fix.** The defaults now match. The admin dashboard also grew a service-health
indicator, because "ML working" and "ML down" were otherwise indistinguishable.

**Test debt this exposed.** Both recommendation fallback tests asserted
`source == "fallback"` while relying on nothing listening on port 8001 — they
passed by accident and broke the moment the ML service was running. They now
patch the client explicitly, and two new tests cover the ML path itself.

---

## 6. The forecaster shipped a model fitted one year behind its own metadata

**Symptom.** The 2026 forecast projected 6.5M arrivals against a real-world
figure nearer 1.15M.

**Root cause, in two parts.**

1. `train_forecast.py` registered the **evaluation** model — fitted on 2021-2023
   so its metrics were honest — while the artifact recorded `last_year = 2024`
   from the full series. Serving therefore extrapolated one extra year of
   compounding growth on every request.
2. The dashboard defaulted to the current calendar year, compounding it further.

**Fix.** Evaluation and serving models are now separate: metrics still come from
the held-out fit, but the registered artifact is refitted on the full series.
The result matches reality much better — the 2025 projection went from 2.25× the
previous year to **1.64×**, against an observed year-on-year growth of 1.62×.

The API also reports `last_observed_year`, `horizon_years` and `reliable`, and
the dashboard defaults to the first year past the data and warns when a request
runs beyond it. Covered by a test asserting the default horizon is reliable and
a three-year horizon is flagged.

---

## 7. An unrecognised region turned a 5.7x overcharge into "not a scam"

**Symptom.** `POST /trust/price-check/` with `region: "Everest"` answered
`is_likely_scam: false` for a quote of 25,000 NPR against a benchmark of 4,293.
The same request with `region: "Everest/Khumbu"` correctly returned
`Likely Scam`.

**Root cause.** The catalogue stores the dataset's compound region names, so the
canonical value is `Everest/Khumbu`. `PricingBenchmark.fair_price_for` filtered
on `region__name__iexact`, found nothing for `Everest`, and returned `None`.
`check_price` then took an early return that reported "no benchmark" — **and
never called the analytics-engine at all**, even though that service holds its
own benchmark table and would have answered.

**Why it hid.** Three things lined up. The unit tests only ever passed region
names they had just created in a fixture, so an alias was never tried. The
response was a clean `200` with a plausible body. And the failure direction was
"nothing to worry about", which is the one outcome nobody investigates. This is
the same shape as defect 5: graceful degradation covering for a real fault, but
worse, because here the degraded answer is the reassuring one.

**Fix.** Three changes in `src/trust/services.py` and `src/catalog/models.py`:

1. `Region` names are resolved through their `/` segments, so `Everest`,
   `Khumbu` and `everest` all reach `Everest/Khumbu`.
2. `fair_price_for` now falls back progressively — (service, region, season) ->
   (service, region) -> (service) — and reports which level answered, matching
   what the analytics-engine already did. The explanation line says "across
   Nepal" rather than naming a region it did not actually use.
3. When there is no local benchmark, the ML service is asked anyway. If nothing
   can answer, the result is `severity: "Unknown"` instead of a silence that
   reads as "Fair".

The same pass fixed a smaller inconsistency: the response could carry two
different shortfall figures for one quote, because the explanation list used the
region-scoped benchmark while `fair_wage_message` came from the model's national
one. The local message now wins, and either service raising the wage flag is
enough to raise it.

**Test debt this exposed.** Five tests were added: four parametrised over region
aliases, and one asserting that an unknown region still flags an overcharge and
says which benchmark it used.

---

## What this says about the testing approach

The thesis already notes that automated coverage was thin. This exercise shows
the specific shape of the risk: the failures were not in complicated logic but
in **wiring** — a settings default, a URL kwarg, a mismatched key, which model
object got saved. Unit tests over individual functions would not have caught any
of them.

Three kinds of test were added in response, and each maps to a defect class:

| Test | Catches |
|---|---|
| Contract test over the URL conf | Handler-signature and routing mistakes, for every current and future route |
| Client-patched integration tests | Behaviour differences between the ML path and the fallback path |
| Horizon assertions on the forecaster | A model being served outside the range its metrics describe |
| Alias and unknown-value cases on lookups | Vocabulary drift between two services that share a dataset |

Counts after this work: **40 core-engine tests, 15 analytics-engine tests**, up
from 26 and 14, with the increase concentrated on the wiring rather than on more
unit coverage of already-working functions.

One more pattern worth naming, because defects 5 and 7 share it. Both were
fallbacks doing their job so well that a real fault produced a calm, plausible,
200-status answer. A fallback should always say which path produced the result,
and a safety feature should never be allowed to fail in the reassuring
direction. Both rules are now enforced in code rather than remembered.
