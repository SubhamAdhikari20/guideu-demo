# GuideU — Data Strategy & Dataset Mapping

The platform is developed against a **synthetic, relational, 500k-row dataset**
(`Travel Planning/`) generated with research-informed correlations and a fixed
seed (`20240519`). It is synthetic by design — see the dataset README's ethics
statement — which sidesteps privacy risk while preserving learnable signal.

## Dataset → service ownership

| Dataset file | Rows | Primary owner | How it is used |
|---|---:|---|---|
| `tourists.csv` | 40,000 | core-engine (`catalog.SyntheticTourist`* / accounts) | User profiles + latent survey scores; the central recommender input. |
| `verified_guides.csv` | 8,000 | core-engine `catalog.GuideRegistry` | NTB/IFMGA/NATHM registry; basis for verified-guide trust + ranking. |
| `trekking_routes.csv` | 2,000 | core-engine `catalog.TrekkingRoute` | Route catalog: permits, difficulty, altitude, seasons, badge points. |
| `cultural_events.csv` | 4,000 | core-engine `catalog.CulturalEvent` | Festival calendar for discovery + gamification. |
| `pricing_benchmarks.csv` | 85,000 | core-engine `catalog.PricingBenchmark` | Fair-price ranges per (service, region, season) — anti-scam ground truth. |
| `bookings.csv` | 95,000 | analytics-engine (training) | Historical transactions for recommender + demand signals. |
| `recommendation_interactions.csv` | 140,000 | analytics-engine (training) | view/wishlist/book/rate/share/complete — collaborative-filtering signal. |
| `scam_reports.csv` | 35,000 | analytics-engine (training) | Labeled overcharge reports; `was_flagged_by_app` is the scam classifier target. |
| `gamification_log.csv` | 31,000 | analytics-engine (`tourist_segments`) | Badge/points affinity per segment. |
| `tourist_arrivals.csv` | 60,000 | analytics-engine (`arrivals_forecaster`) | Aggregated arrivals time series (2021–2024) → a 48-month series. |
| `recommendation_flat.csv` | 95,000 | analytics-engine (profiling) | Pre-joined wide table used for the data profiling in §2. |

All ten tables now feed a model or the profiling that shaped one. Before the ML
work, three of them were unreferenced by any code path.

\* The synthetic tourist rows are reference/training records, **not** live app
credentials. The ingestion command loads them into a reference table so the
catalog and the ML feature store can join against them without creating
fake login accounts. Real app users come from `authentication.User`.

## What the data actually supports (profiled before modelling)

The dataset documentation advertises several signals. Profiling found that **only
some of them exist**, and the modelling was designed around what survived. Full
tables in [RESEARCH_FINDINGS.md](RESEARCH_FINDINGS.md) §2.

| Claimed signal | Profiling result |
|---|---|
| Adventure score → route difficulty | **Real and strong** — 1.81 → 3.25 across quintiles |
| Overcharge ratio → flag | **Real** — deterministic step at ratio ≈ 1.25 |
| Certification → guide rating | **Real** — IFMGA 4.55, City Guide 3.85 |
| Budget band → route cost | **Absent** — 2,112 / 2,109 / 2,107 / 2,094 USD |
| Culture score → region | **Absent** — region shares differ < 2pp |
| Nature score → altitude | **Absent** — ~4,500 m across every quintile |
| Fitness / experience → difficulty | **Absent** — all ≈ 2.52 |

Two structural properties matter as much as the signals:

- **Sparsity hostile to collaborative filtering.** Route-interaction density is
  0.00106 and users average 1.15 positive events. A user's own region history
  predicts their next region *worse* than guessing the most popular region
  (23.3% vs 36.9%), so matrix factorisation was not pursued.
- **A cloned catalog.** 2,000 route rows carry 375 distinct names covering only
  **26 real treks** sold as variants. This caps route-level ranking precision
  independently of model quality, so metrics are reported at two granularities.

## The headline AI features

1. **Anti-scam price benchmarking** — binary classification on
   `was_flagged_by_app` (~21.4% positive) from `service_type`, `region`, `season`
   and the quoted price. `overcharge_ratio` and `benchmark_price_npr` are
   **excluded as leakage** (the label is a deterministic function of the ratio),
   and `nationality`/`continent` are **excluded as protected attributes**.
2. **Personalised recommendations** — a learned pointwise ranker over
   (tourist × route) pair features. The model concentrates its weight on the
   adventure/difficulty match and discards the signals profiling showed to be
   absent.
3. **Verified-guide ranking** — supervised prediction of the 1–5 rating a
   specific tourist would give a specific guide, with region/language treated as
   hard requirements and verification status enforced outside the model.
4. **Demand forecasting** — monthly arrivals from `tourist_arrivals.csv`.
5. **Cold-start segmentation** — k-means over the five survey scores, reported
   with its weak silhouette rather than presented as discovered personas.

## Raw → cleaned → features

The analytics-engine keeps a strict separation:

```
services/analytics-engine/
  data/raw/         # symlink or copy of Travel Planning (read-only)
  data/processed/   # cleaned, typed parquet written by the cleaning step
  features/         # feature engineering (fit scores, recency, encoders)
  artifacts/        # trained model binaries + model_registry.json
  mlruns/           # MLflow tracking store
```

## Ingestion into the core engine

`python manage.py seed_from_dataset --dataset-dir "Travel Planning"` performs an
idempotent, chunked bulk load of the **catalog** tables (regions, routes, guide
registry, cultural events, pricing benchmarks) into PostgreSQL. Transactional
tables (bookings/interactions/scam reports) stay in the dataset for ML training;
a small demo subset can be materialised with `--with-demo-bookings`.

## Temporal split for honest evaluation

Models train on **2021–2023** and test on **2024** to avoid leakage and reflect
deployment. Model choice and decision thresholds are fixed on a **2023 validation
year** so the reported operating point is never tuned on the split it reports.

Metrics: Precision@K / Recall@K / NDCG@K / MAP@K / MRR@K (recommender);
ROC-AUC / PR-AUC / F1 / **Brier** (scam — calibration matters because the app
shows a probability to a user); RMSE / MAE / R² (guide matching);
MAE / RMSE / MAPE (forecasting); silhouette plus an extrinsic ANOVA
(segmentation).
