# GuideU — Machine Learning

The `analytics-engine` (FastAPI) implements GuideU's AI features against the
synthetic Travel Planning dataset. Everything below is **reproducible**:
`python -m training.run_all --report artifacts/training_report.json` regenerates
the artifacts and every number on this page.

Five models are trained. Each is registered with a model card
(`artifacts/model_registry.json`, optional MLflow) and each is reported **against
at least one baseline scored through the same harness** — a metric with no
baseline beside it says nothing about whether the model was worth building.

| Model | Task | Algorithm | Headline result |
|---|---|---|---|
| `route_recommender` | Rank 2,000 treks for a tourist | Logistic regression, pointwise ranker | Hit-rate@10 **1.63×** popularity |
| `scam_classifier` | Flag an overcharged quote | Gradient boosting | **F1 0.980**, Brier 0.006 |
| `guide_ranker` | Predict a tourist's rating of a guide | Ridge regression | RMSE **0.655** vs 0.688 mean |
| `arrivals_forecaster` | Forecast monthly arrivals | Log-linear trend + seasonality | **MAPE 17.2%** vs 38.6% naive |
| `tourist_segments` | Cold-start personas | K-means (k=4) | Silhouette 0.13 — *reported as weak* |

## Method

- **Temporal splits, never random.** Models train on 2021–2023 and are tested on
  2024. A random split would leak the future into training.
- **Hyper-parameters and thresholds are chosen on a validation year (2023)**, not
  on the test year. Where that choice turns out to be wrong on the test year (it
  does, for the forecaster) the disagreement is reported rather than smoothed.
- **Baseline-first.** A simple model is fitted before a complex one, and the
  complex one is only adopted if it wins on the validation split.

---

## What the dataset actually supports

Before any modelling, the ten tables were profiled. Three findings shaped every
design decision that follows, and two of them are negative.

**1. Exactly one strong preference signal exists.** Splitting the 11,900 positive
route interactions by the tourist's `pref_adventure_score` quintile:

| Adventure quintile | Mean difficulty | Mean cost (USD) | Mean altitude (m) |
|---|---|---|---|
| 1 (lowest) | 1.81 | 1,748 | 4,038 |
| 2 | 2.16 | 1,919 | 4,276 |
| 3 | 2.53 | 2,102 | 4,544 |
| 4 | 2.88 | 2,286 | 4,782 |
| 5 (highest) | 3.25 | 2,470 | 4,912 |

Difficulty rises cleanly with the adventure score. Cost and altitude ride along
with it because they correlate with difficulty, not independently.

**Every other advertised signal is flat.** Budget band does not predict route
cost (2,112 / 2,109 / 2,107 / 2,094 USD for Budget / Comfort / Luxury /
Mid-range). Culture score does not predict region. Nature score does not predict
altitude (4,510 / 4,507 / 4,508 / 4,525 / 4,498 across quintiles). Neither
fitness level nor experience level predicts difficulty (all ≈ 2.52). This matters
because the original hand-weighted recommender spent 20% of its score on budget
fit and 20% on season — i.e. 40% of its ranking weight on noise.

**2. Feedback is far too sparse for collaborative filtering.** 33,154 users
touched 2,000 routes, a matrix density of 0.001, and users average **1.15**
positive route events. Only 1,398 of 10,344 users have more than one. There is
almost nothing for user-user or item-item similarity to work with, and a check
confirmed it: a user's 2021–2023 region history predicts their 2024 region only
23.3% of the time, *worse* than always guessing the most popular region (36.9%).
Collaborative filtering was therefore not pursued — not because it is hard, but
because the data cannot support it.

**3. The catalog is cloned, twice over.** 2,000 route rows carry only 375
distinct route names, and those 375 names are **26 real treks** sold as variants
("Everest Base Camp (Classic)", "(Budget)", "(Express)"…). This caps route-level
precision structurally: a model can identify the right trek and still miss the
exact `route_id` the tourist booked. Metrics are therefore reported at two
granularities throughout — route level and variant-concept level.

---

## 1. Route recommender

**Task.** Rank the catalog for a tourist.
**Model.** Logistic regression over (tourist × route) pair features, trained
pointwise: each observed positive is paired with 8 sampled negatives. Pointwise +
negative sampling is the simplest formulation that still learns a ranking, and it
keeps the coefficients readable.

**Features.** Five survey scores, four normalised route attributes
(difficulty, cost, altitude, duration), three cross terms (`gap_adventure`,
`gap_altitude`, `gap_cost`) and a train-period popularity prior.

### The learned weights confirm the data profile

| Feature | Coefficient (standardised) |
|---|---|
| `gap_adventure` | **−1.5924** |
| `popularity` | +0.1485 |
| `pref_adventure_score` | −0.0840 |
| `duration_norm` | +0.0536 |
| `gap_cost` | +0.0307 |
| *(remaining 8 features)* | all \|β\| < 0.03 |

The model puts essentially all its weight on the one term the data supports and
drives the rest to zero. **This is the argument for learning the weights rather
than setting them**: given the same features, the hand-tuned heuristic assigned
40% of its score to signals the learned model correctly discards.

### Results (test = 2024 positives, 2,898 users)

| Strategy | HR@10 | NDCG@10 | concept HR@10 | concept MRR@10 |
|---|---|---|---|---|
| Random | 0.0069 | 0.0029 | 0.0317 | 0.0092 |
| **Popularity (baseline)** | **0.0083** | **0.0039** | **0.0462** | **0.0133** |
| Hand-weighted heuristic (previous) | 0.0090 | 0.0040 | 0.0680 | 0.0206 |
| **Learned ranker** | **0.0135** | **0.0061** | **0.0721** | **0.0215** |
| Learned + variant de-dupe | 0.0138 | 0.0062 | 0.0745 | 0.0218 |

The learned ranker beats popularity by **1.63×** on hit-rate@10 and **1.56×** at
concept level; the previous heuristic managed only 1.08×.

### The diversity trade-off (and what ships)

Because 26 treks hide behind 2,000 rows, an unconstrained top-10 can be four
packagings of the same trail. Capping variants per base trek fixes that, at a
measured cost:

| Cap | HR@10 | concept HR@10 | Lift vs popularity |
|---|---|---|---|
| none (variant de-dupe) | 0.0138 | 0.0745 | 1.67× |
| max 3 per trek — **deployed** | 0.0114 | 0.0666 | **1.38×** |
| max 2 per trek | 0.0104 | 0.0625 | 1.25× |
| max 1 per trek | 0.0086 | 0.0562 | 1.04× |

Collapsing to one row per trek destroys the gain — it throws away the model's
ability to pick *which* packaging suits the traveller, landing back at baseline.
A cap of **3** is deployed: it guarantees at least four distinct treks in a
top-10 while keeping a 1.38× lift. Reported both ways, the model's own ranking
quality is 1.63× and the served endpoint achieves 1.38×.

**Absolute numbers are low, and honestly so.** With 2,000 items, ~1.15 positives
per user and a cloned catalog, a hit-rate@10 of 1.4% is what this data allows.
The defensible claim is the *relative* one: personalisation beats popularity by a
clear margin, and the margin comes from a signal the model found by itself.

**Traceability.** Every recommendation returns per-feature contributions
(standardised value × coefficient) rendered as plain-language reasons, so the
"why am I seeing this?" text is generated from the same arithmetic that produced
the ranking — not a narrative written next to it.

---

## 2. Anti-scam classifier

**Task.** Predict `was_flagged_by_app` for a quoted price.
**Model.** Gradient boosting (`HistGradientBoostingClassifier`), selected over a
logistic-regression baseline on the 2023 validation year. Decision threshold
**0.45**, also chosen on validation.

### Features, and what is deliberately excluded

- **Used:** `service_type`, `region`, `season`, `quoted_price_npr`, `log price`.
  Season is derived from `reported_date`; it is available at request time too.
- **Excluded — leakage:** `overcharge_ratio`, `benchmark_price_npr`,
  `scam_severity`. In the generator the label is a deterministic step function of
  the ratio (0 below ≈1.25, 1 above — verified: flag rate is exactly 0.0 in every
  bucket under 1.25 and exactly 1.0 in every bucket above 1.3). Feeding the ratio
  back would produce a meaningless perfect score. Excluding it forces the model to
  learn price bands per service and region, which is what the app actually needs.
- **Excluded — protected:** `nationality`, `continent`. The dataset intentionally
  simulates tourist-price discrimination; these are used only in the audit.

### Results (test = 2024, n = 8,542)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC | Brier |
|---|---|---|---|---|---|---|---|
| Majority baseline | 0.786 | 0.000 | 0.000 | 0.000 | 0.500 | 0.214 | 0.214 |
| Logistic regression | 0.986 | 0.960 | 0.973 | 0.966 | 0.999 | 0.996 | 0.049 |
| **Gradient boosting** | **0.991** | **0.979** | **0.981** | **0.980** | 0.998 | **0.997** | **0.006** |

Brier score is the reason gradient boosting was chosen despite near-identical
AUC. The app shows a *probability* to a user, so calibration matters as much as
ranking, and 0.006 versus 0.049 is an 8× improvement in calibration error.

### Cold-cell generalisation

The ordinary split lets the model memorise price bands it has already seen. The
harder, more realistic test holds out **60 entire (service_type, region)
combinations** — quotes from cells the model has never encountered:

| Model | ROC-AUC | F1 |
|---|---|---|
| Logistic regression | 0.9989 | 0.891 |
| **Gradient boosting** | **0.9989** | **0.958** |

Performance holds. The model has learned the shape of the price/service
relationship rather than a lookup table, which is what makes it useful for a
quote with no exact benchmark.

### Fairness audit (and an honest reading)

Per-continent flag rates on the 2024 test set:

| Continent | n | Model flag rate | Actual rate |
|---|---|---|---|
| East Asia | 1,874 | 0.154 | 0.154 |
| Europe | 1,939 | 0.306 | 0.302 |
| Latin America | 139 | 0.180 | 0.180 |
| Middle East | 150 | 0.153 | 0.147 |
| North America | 826 | 0.315 | 0.320 |
| Oceania | 387 | 0.305 | 0.308 |
| South Asia | 3,227 | 0.162 | 0.162 |

Flag-rate disparity is **0.1615**, above the 0.15 review gate — so the gate
correctly routes the model to **review, not silent deployment**. The reading:
the model's flag rate tracks each group's *actual* overcharge rate to within
0.006 everywhere. European and North American tourists really are quoted higher
prices in this data, so a fair overcharge detector *should* flag their quotes
more often. The disparity lives in the simulated world, not in the model — and
with protected attributes excluded, the model is protecting those tourists
rather than profiling them. See [ethics-and-fairness.md](ethics-and-fairness.md).

---

## 3. Guide match-quality model

**Task.** Predict the 1–5 rating a *particular* tourist will give a *particular*
guide, then rank a shortlist by it. This replaces a fixed weighted sum that could
not be evaluated because nothing in it came from the data.

**Model.** Ridge regression over guide credentials (certification, verification
status, years of experience, registry rating, trips completed, language and
region breadth) plus the tourist's own profile. Gradient boosting was tried and
lost.

### Results (test = 2024, n = 984 ratings)

| Model | RMSE | MAE | R² |
|---|---|---|---|
| Predict the global mean | 0.688 | 0.516 | 0.000 |
| Rank by the guide's own average rating | 0.705 | 0.563 | −0.051 |
| **Ridge (deployed)** | **0.655** | **0.511** | **0.093** |
| Gradient boosting | 0.692 | 0.549 | −0.011 |

The gain is real but small: **4.8%** better RMSE than predicting the mean. The
more interesting result is that the obvious no-model strategy — "just show the
best-rated guides" — is **worse than the global mean** (0.705 vs 0.688). A
guide's overall rating is a poor predictor of how one specific traveller will
rate them, which is the case for personalised matching, modest as the effect is.

**Not learned, applied afterwards:** region coverage and language are treated as
hard requirements, not tastes, and an expired licence is demoted regardless of
predicted rating. Ranking an unverified guide above a verified one on predicted
score would undercut the platform's entire premise.

---

## 4. Arrivals demand forecaster

**Task.** Forecast monthly national tourist arrivals. Uses
`tourist_arrivals.csv` (60,000 cohort rows → a 48-month series, 2021–2024).

**Model.** Ordinary least squares on `log(arrivals) ~ time + month indicators`,
fitted on the **trailing 24 months**. Logs make seasonality multiplicative, which
is what a recovering series needs — a month is a percentage of the year's level,
not a fixed number of visitors.

The 24-month window is a **domain decision made before looking at the test year**:
yearly totals run 100k → 488k → 936k → 1.51M, so 2021 is a COVID-recovery anomaly
operating at a fifteenth of 2024's volume and would distort any trend fitted
through it.

### Results (test = 2024, 12 months)

| Method | MAE | RMSE | MAPE |
|---|---|---|---|
| Mean of last 12 months | 64,164 | 70,976 | 53.0% |
| Seasonal naive (same month last year) | 48,006 | 51,667 | 38.6% |
| Seasonal naive × YoY growth | 23,666 | 26,624 | 17.8% |
| **Log-linear trend + seasonality** | **22,515** | **25,076** | **17.2%** |

### The honest caveat

On the **2023 validation year** the ranking inverts completely — seasonal naive
wins at 47.6% MAPE while the log-trend model reaches 155%, because with only
2021–2022 to learn from, the trend is fitted through the 4.85× recovery spike and
extrapolates it forward.

**Three years of a recovery-distorted series is not enough data for stable model
selection.** The deployed model wins on the genuine held-out year and is
principled, but the validation year disagrees, and that is reported rather than
hidden. This is why every forecast is served with its error band and the
instruction to treat the band, not the point estimate, as the forecast.

---

## 5. Tourist segmentation

**Task.** Give a brand-new user with no history a starting profile better than
the population average.
**Model.** K-means (k = 4) over the five survey scores.

### The clusters are weak, and this is reported as a finding

| k | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| Silhouette | 0.138 | 0.131 | 0.133 | 0.133 | 0.138 | 0.136 | 0.137 |

Silhouette sits near 0.13 for **every** k. There is no natural cluster structure
— the generator drew the five preference scores close to independently, so the
preference space is a diffuse cloud. Choosing k = 4 is picking a convenient
partition, not discovering personas, and the segments are labelled accordingly.

### Extrinsic validation

Geometry is not the only test. Do the segments predict *behaviour*?

| Segment | Name | Size | Mean booked difficulty |
|---|---|---|---|
| 0 | Budget-conscious / Nature-loving | 10,276 | 2.587 |
| 1 | Risk-tolerant | 10,047 | 2.514 |
| 2 | Urban-leaning / Budget-conscious | 9,503 | 2.544 |
| 3 | Comfort-spending / Safety-first | 10,174 | 2.450 |

One-way ANOVA on booked-route difficulty: **F = 21.01, p = 1.4 × 10⁻¹³** — the
segments do differ. But the spread between the extreme segments is 0.137 against
a pooled SD of 0.699, i.e. **Cohen's d ≈ 0.20**, a small effect.

Statistically unambiguous, practically small. The segments are worth using as a
cold-start default and are not worth describing to a user as their travel
personality.

---

## Fair-wage protection (a rule, not a model)

Price transparency has an asymmetric failure mode. Publishing a fair range helps
a tourist spot an overcharge — and equally helps them anchor every negotiation at
the bottom of that range. For guides and porters, that floor is a daily wage.

`inference/pricing.wage_check` therefore flags under-quoting as well as
over-quoting. A quote below 95% of the fair floor for a **labour** service
(Licensed Guide, Porter) raises `below_fair_wage`, and the app renders it as its
own outcome rather than as a bargain. Permits, meals and transport are exempt —
a cheap permit is a fee, not somebody's underpaid labour. The rule is enforced in
both the analytics-engine and the core-engine fallback path, and is covered by
tests in both services.

---

## Reproducibility & registry

```bash
cd services/analytics-engine
python -m training.run_all --report artifacts/training_report.json
python -m training.run_all --only route_recommender    # one model
```

Artifacts, metrics and full baseline comparisons land in
`artifacts/model_registry.json` and `artifacts/training_report.json`. Set
`MLFLOW_TRACKING_URI` to also log runs to MLflow. `GET /api/v1/models` exposes
the live registry to the admin dashboard.

## Serving

| Endpoint | Model |
|---|---|
| `POST /api/v1/recommendations/routes` | `route_recommender` (+ reasons) |
| `POST /api/v1/scam/score` | `scam_classifier` (+ fair-wage rule) |
| `POST /api/v1/guides/rank` | `guide_ranker` |
| `POST /api/v1/segments/assign` | `tourist_segments` |
| `POST /api/v1/forecast/arrivals` | `arrivals_forecaster` |
| `POST /api/v1/pricing/benchmark` | dataset aggregation |
| `GET /api/v1/models` | the registry |

Every endpoint degrades to an explainable fallback when its artifact is missing,
so the service boots and serves before anything has been trained.
