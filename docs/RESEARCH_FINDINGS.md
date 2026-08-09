# GuideU — Research Findings

**Applying recommendation, risk scoring and forecasting to a sparse,
informal-market tourism dataset.**

This document is the evidence base for the thesis evaluation chapter. It records
what the data supports, what was built, what the models achieved against
baselines, and — at equal length — what did not work. Every figure is
reproducible with `python -m training.run_all` from
`services/analytics-engine`; the raw output is committed at
`artifacts/training_report.json`.

- **Technical detail:** [ml.md](ml.md)
- **Plain-English summaries:** [MODELS_SIMPLE_OVERVIEW.md](MODELS_SIMPLE_OVERVIEW.md)
- **Fairness discussion:** [ethics-and-fairness.md](ethics-and-fairness.md)

---

## 1. Study design

### 1.1 Research questions addressed here

**RQ1 (technical).** To what extent can machine-learning services — a
personalised recommender together with price-benchmarking and scam-risk models —
provide accurate and useful decision support for tourists planning travel in
Nepal, when evaluated against sensible baselines on the project dataset using a
temporal split?

**RQ2 (ethical).** What ethical risks arise when an AI-driven platform mediates
trust between tourists and informal-sector providers, and how effectively can
those risks be mitigated within the design of such a platform?

### 1.2 Hypotheses

| | Hypothesis | Verdict |
|---|---|---|
| **H1** | The personalised recommender will outperform a non-personalised popularity baseline by a practically meaningful margin | **Supported**, with a caveat on absolute scale |
| **H2** | The scam-risk model will reach ≥ 90% accuracy/F1 on held-out data | **Supported** (99.1% accuracy, F1 0.980) |
| **H3** | Fairness-aware adjustments can be applied without a large loss in predictive usefulness | **Supported**, but the test was weaker than intended |

### 1.3 Evaluation protocol

- **Temporal split throughout.** Train 2021–2023, test 2024. A random split would
  leak future interactions into training and inflate every number reported here.
- **Validation year for all selection.** Model choice and decision thresholds are
  fixed on 2023 before the 2024 test set is touched.
- **Baselines scored through the identical harness.** Random, popularity,
  majority class, seasonal naive, global mean — as appropriate to each task.
- **Reported both ways.** Where a product constraint costs accuracy, both the
  unconstrained model score and the deployed score are given.

### 1.4 The dataset

Synthetic, relational, 500,000 rows across ten tables (`Travel Planning/`), fixed
seed `20240519`. Synthetic by design: a pre-launch platform has no interaction
history — the cold-start problem described by Lika et al. (2014) — and generating
data avoids processing real guides' identities and livelihoods without consent.
The cost is external validity, discussed in §6.

**All ten tables are now used.** Before this work, three (`tourist_arrivals`,
`gamification_log`, `recommendation_flat`) were unreferenced by any model.

---

## 2. Data profiling: what the dataset will and will not support

Modelling decisions were made after profiling, not before. Three findings drove
everything downstream — and two are negative results.

### 2.1 Finding A — exactly one preference signal is learnable

Splitting the 11,900 positive route interactions by the tourist's
`pref_adventure_score` quintile:

| Adventure quintile | n | Mean difficulty | Mean cost (USD) | Mean altitude (m) |
|---|---|---|---|---|
| 1 (lowest) | 2,390 | 1.81 | 1,748 | 4,038 |
| 2 | 2,390 | 2.16 | 1,919 | 4,276 |
| 3 | 2,370 | 2.53 | 2,102 | 4,544 |
| 4 | 2,379 | 2.88 | 2,286 | 4,782 |
| 5 (highest) | 2,371 | 3.25 | 2,470 | 4,912 |

Monotonic and strong. Cost and altitude follow because both correlate with
difficulty, not because they carry independent signal.

**Every other advertised relationship is flat:**

| Claimed signal | Result | Verdict |
|---|---|---|
| Budget band → route cost | 2,112 / 2,109 / 2,107 / 2,094 USD across four bands | **No signal** |
| Culture score → region | Region shares differ < 2pp across quintiles | **No signal** |
| Nature score → altitude | 4,510 / 4,507 / 4,508 / 4,525 / 4,498 m | **No signal** |
| Fitness level → difficulty | 2.535 / 2.528 / 2.524 / 2.522 | **No signal** |
| Experience level → difficulty | 2.546 / 2.524 / 2.527 / 2.515 | **No signal** |

The implication is direct: the previous hand-weighted recommender allocated 45%
of its score to adventure fit (correct) and **40% to budget fit and season fit —
two dimensions carrying no information whatsoever.**

### 2.2 Finding B — the data cannot support collaborative filtering

| Property | Value |
|---|---|
| Users with route interactions | 33,154 |
| Items | 2,000 |
| Matrix density | **0.00106** |
| Mean positive events per user | **1.15** |
| Users with > 1 positive | 1,398 of 10,344 (13.5%) |

At 1.15 positives per user there is almost no co-occurrence for user-user or
item-item similarity to exploit. This was tested rather than assumed: **a user's
2021–2023 region history predicts their 2024 region 23.3% of the time, against
36.9% for simply guessing the most popular region.** History is worse than
ignoring history.

Matrix factorisation was therefore not pursued. This is a data-driven decision,
not an avoidance of difficulty — and it aligns with Ferrari Dacrema, Cremonesi &
Jannach (2019), whose reproducibility analysis found that carefully-tuned simple
baselines frequently outperform elaborate neural recommenders.

### 2.3 Finding C — the catalog is cloned at two levels

| Level | Distinct values |
|---|---|
| Route rows (`route_id`) | 2,000 |
| Route names (variants) | 375 |
| **Base treks** | **26** |

Each real trek ("Everest Base Camp") appears as ~15 named variants ("(Classic)",
"(Budget)", "(Express)"), each duplicated ~5–6 times. This places a **structural
ceiling on route-level precision**: a model can identify the right trek and still
miss the exact `route_id` booked.

This is the single most important methodological caveat in the evaluation, and it
is a property of the data generator rather than of any model. Metrics are
therefore reported at two granularities throughout.

---

## 3. RQ1 results

### 3.1 Route recommendation (H1)

**Model.** Logistic regression over (tourist × route) pair features, trained
pointwise with 8 sampled negatives per positive.

**Result — the model recovers the data profile unaided.** Standardised
coefficients:

| Feature | β |
|---|---|
| `gap_adventure` | **−1.5924** |
| `popularity` | +0.1485 |
| `pref_adventure_score` | −0.0840 |
| `duration_norm` | +0.0536 |
| `gap_cost` | +0.0307 |
| remaining 8 features | all \|β\| < 0.03 |

Given thirteen features, the model concentrates its weight on the one the data
supports and drives the rest toward zero. **This is the strongest single argument
in the project for learning parameters rather than assigning them.** The hand-set
weights spent 40% of the score on noise; the learned model found that out from
the data in one fit.

**Ranking performance** (test = 2024 positives, 2,898 users, K = 10):

| Strategy | HR@10 | NDCG@10 | MAP@10 | concept HR@10 | concept MRR@10 |
|---|---|---|---|---|---|
| Random | 0.0069 | 0.0029 | — | 0.0317 | 0.0092 |
| **Popularity (baseline)** | **0.0083** | **0.0039** | 0.0026 | **0.0462** | **0.0133** |
| Hand-weighted heuristic (prior work) | 0.0090 | 0.0040 | 0.0026 | 0.0680 | 0.0206 |
| **Learned ranker** | **0.0135** | **0.0061** | **0.0040** | **0.0721** | **0.0215** |
| Learned + variant de-dupe | 0.0138 | 0.0062 | 0.0040 | 0.0745 | 0.0218 |

**H1 verdict: supported.** The learned ranker achieves **1.63× the popularity
baseline** on hit-rate@10 (1.56× at concept level). The previous heuristic
managed 1.08× — within noise of the baseline it was meant to beat.

**The accuracy/diversity trade-off.** Because 26 treks hide behind 2,000 rows, an
unconstrained shortlist can be four packagings of one trail. Capping variants per
trek has a measured price:

| Variants per trek | HR@10 | concept HR@10 | Lift vs popularity |
|---|---|---|---|
| Unconstrained | 0.0138 | 0.0745 | 1.67× |
| **max 3 — deployed** | **0.0114** | **0.0666** | **1.38×** |
| max 2 | 0.0104 | 0.0625 | 1.25× |
| max 1 | 0.0086 | 0.0562 | 1.04× |

Full collapse to one row per trek returns the model to baseline: it removes the
model's ability to choose *which* packaging fits. A cap of 3 is deployed —
at least four distinct treks per top-10, 1.38× lift retained.

**Honest limitation.** Absolute hit-rate@10 of ~1.4% is low. With 2,000 items,
1.15 positives per user and a cloned catalog, this is close to what the data
permits, and the defensible claim is relative, not absolute. Cremonesi, Koren &
Turrin (2010) established that error metrics such as RMSE do not transfer to
top-N tasks and that precision/recall on ranked lists is the appropriate measure;
their work also established the popularity baseline as the bar a top-N recommender
must clear — which is why it is the comparator throughout.

### 3.2 Anti-scam classification (H2)

**Model.** Gradient boosting, selected over logistic regression on the 2023
validation year; decision threshold 0.45, also validation-selected.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | PR-AUC | Brier |
|---|---|---|---|---|---|---|---|
| Majority baseline | 0.786 | 0.000 | 0.000 | 0.000 | 0.500 | 0.214 | 0.214 |
| Logistic regression | 0.986 | 0.960 | 0.973 | 0.966 | 0.999 | 0.996 | 0.049 |
| **Gradient boosting** | **0.991** | **0.979** | **0.981** | **0.980** | 0.998 | **0.997** | **0.006** |

**H2 verdict: supported**, comfortably — 99.1% accuracy and F1 0.980 against a
90% target. For context, Ott et al. (2011) found automated deception classifiers
reaching ~90% on review text where human judges performed near chance.

**Model selection turned on calibration, not accuracy.** ROC-AUC is effectively
tied (0.998 vs 0.999). The app displays a *probability* to a user, so calibration
is a first-order concern, and the Brier score differs by 8× (0.006 vs 0.049).
Selecting on AUC alone would have shipped the worse-calibrated model.

**Two exclusions make the task honest:**

- *Leakage.* The label is a deterministic step function of `overcharge_ratio` —
  verified empirically: the flag rate is exactly 0.000 in every ratio bucket below
  1.25 and exactly 1.000 in every bucket above 1.30. Including the ratio or the
  benchmark would yield a meaningless perfect score.
- *Protected attributes.* `nationality` and `continent` are excluded from the
  feature set entirely and used only in the audit.

**Cold-cell generalisation** — 60 entire (service_type, region) combinations held
out, so the model scores quotes from cells it has never seen:

| Model | ROC-AUC | F1 |
|---|---|---|
| Logistic regression | 0.9989 | 0.891 |
| **Gradient boosting** | **0.9989** | **0.958** |

Performance holds. The model has learned the structure of the price/service
relationship rather than memorising a lookup table — which is what makes it
usable for a quote with no exact benchmark, the realistic deployment case.

### 3.3 Guide match quality

| Model | RMSE | MAE | R² |
|---|---|---|---|
| Global mean | 0.688 | 0.516 | 0.000 |
| **Guide's own average rating** | **0.705** | **0.563** | **−0.051** |
| **Ridge (deployed)** | **0.655** | **0.511** | **0.093** |
| Gradient boosting | 0.692 | 0.549 | −0.011 |

A 4.8% RMSE improvement over the mean — modest and reported as such.

**The more valuable result is the second row.** The intuitive no-model strategy —
"rank guides by their star rating" — performs *worse than predicting the average
for everyone*. A guide's aggregate rating is a poor predictor of how a specific
traveller will rate them. This is the empirical case for match-based ranking over
reputation sorting, and it is exactly the kind of comparison that goes unrun in
projects that report only their own model's score.

### 3.4 Demand forecasting

| Method | MAE | RMSE | MAPE |
|---|---|---|---|
| Mean of last 12 months | 64,164 | 70,976 | 53.0% |
| Seasonal naive | 48,006 | 51,667 | 38.6% |
| Seasonal naive × YoY growth | 23,666 | 26,624 | 17.8% |
| **Log-linear trend + seasonality** | **22,515** | **25,076** | **17.2%** |

Error roughly halved against the seasonal naive benchmark that Hyndman &
Athanasopoulos recommend as the standard comparator for seasonal series. The log
transform makes seasonality multiplicative, appropriate when seasonal variation
scales with the level of the series — as it must in a market growing 15× over the
observation window.

**A reported negative result.** On the **2023 validation year the ranking
inverts**: seasonal naive achieves 47.6% MAPE while the deployed model reaches
155%, because fitting on 2021–2022 puts the 4.85× post-COVID recovery spike
inside the trend window.

Three years of a recovery-distorted series provides only two year-on-year growth
observations, which is not enough for stable model selection. The deployed model
wins the genuine held-out year and is principled a priori, but the disagreement
is real and is surfaced in the model card, in the API response, and in the admin
UI, which renders the error band rather than a bare point estimate.

### 3.5 Segmentation

| k | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| Silhouette | 0.138 | 0.131 | 0.133 | 0.133 | 0.138 | 0.136 | 0.137 |

**A flat silhouette curve near 0.13 for every k is itself the finding: there is no
natural cluster structure.** The generator drew the five preference scores close
to independently, producing a diffuse cloud. Selecting k = 4 is choosing a
convenient partition, not discovering personas.

Extrinsic validation asks a different question — do the segments predict
behaviour?

| Segment | Label | Size | Mean booked difficulty |
|---|---|---|---|
| 0 | Budget-conscious / Nature-loving | 10,276 | 2.587 |
| 1 | Risk-tolerant | 10,047 | 2.514 |
| 2 | Urban-leaning / Budget-conscious | 9,503 | 2.544 |
| 3 | Comfort-spending / Safety-first | 10,174 | 2.450 |

ANOVA: **F = 21.01, p = 1.4 × 10⁻¹³**. Unambiguously non-random. But the spread
between extreme segments is 0.137 against a pooled SD of 0.699 — **Cohen's
d ≈ 0.20**, a small effect.

The correct reading: statistically certain, practically minor. Reporting the
p-value alone would have made a 0.2 SD difference sound like a discovery. The
segments are used as a cold-start default and are deliberately **not** surfaced
to users as a travel personality.

### 3.6 RQ1 summary

Machine learning provides **measurable but uneven** decision support here, and
the unevenness is informative:

| Task | Verdict | Why |
|---|---|---|
| Scam risk | **Strong** | Clean labels, dense signal, generalises to unseen cells |
| Forecasting | **Moderate** | Halves naive error, but unstable model selection on 3 years |
| Recommendation | **Modest but real** | 1.63× popularity; capped by sparsity and a cloned catalog |
| Guide matching | **Marginal** | 4.8% over mean — though it beats reputation sorting |
| Segmentation | **Weak** | No natural structure; small behavioural effect |

The pattern is consistent and worth stating plainly: **the models succeed in
proportion to the density of the signal available**, and the platform's
verification and benchmarking features — which depend on structured reference
data — are on firmer ground than its personalisation features, which depend on
behavioural history the market has not yet generated. For a pre-launch platform
in an informal market, that ordering is the practically useful finding.

---

## 4. RQ2 results

### 4.1 Fairness audit of the scam classifier

| Continent | n | Model flag rate | Actual rate | Difference |
|---|---|---|---|---|
| East Asia | 1,874 | 0.154 | 0.154 | 0.000 |
| Europe | 1,939 | 0.306 | 0.302 | +0.004 |
| Latin America | 139 | 0.180 | 0.180 | 0.000 |
| Middle East | 150 | 0.153 | 0.147 | +0.006 |
| North America | 826 | 0.315 | 0.320 | −0.005 |
| Oceania | 387 | 0.305 | 0.308 | −0.003 |
| South Asia | 3,227 | 0.162 | 0.162 | 0.000 |

Flag-rate disparity **0.1615**, exceeding the 0.15 gate — the model is routed to
**review rather than silent deployment**, which is the gate working.

**Interpretation.** The model's flag rate tracks each group's *actual* overcharge
rate to within 0.006 everywhere. European, North American and Oceanian tourists
genuinely are quoted higher prices in this data — a pattern the generator
introduced deliberately to mirror documented tourist-price discrimination. A
detector that equalised flag rates across groups would systematically
under-protect exactly the tourists being overcharged most.

This is a direct instance of Chouldechova's (2017) impossibility result: when
base rates differ between groups, calibration and error-rate balance cannot both
be satisfied, and the choice between them is normative rather than technical.
GuideU's position is stated explicitly: **the model is calibrated to the world
and refuses to use nationality as an input.** The disparity lives in the market
being modelled, not in the classifier.

The mitigation is structural rather than statistical — exclude protected
attributes, always return the benchmark, the ratio and the reasoning, and route
the model to human review when the gate trips. Where a group difference is real,
the honest response is to make it inspectable, not to tune it away.

### 4.2 Fair-wage protection for providers

The ethical risk that runs *toward* providers rather than tourists: publishing a
fair price range helps a traveller detect an overcharge, and equally helps them
anchor every negotiation at the floor of that range. For a guide or a porter, the
floor is a daily wage. Left alone, the platform's transparency would function as
downward wage pressure.

**Implemented.** A quote below 95% of the fair floor for a **labour** service
(Licensed Guide, Porter) raises `below_fair_wage`, and the mobile app renders it
as its own outcome with its own colour and icon — not as a good deal:

> *"This is 45.5% below the fair rate for a licensed guide. Paying under the fair
> range pushes licensed workers out of the market — please consider the fair rate
> of 4,740 NPR."*

Permits, meals and transport are exempt: a cheap permit is a fee, not underpaid
labour. The rule is enforced in the analytics-engine and independently in the
core-engine fallback path, so it survives an ML outage, and is covered by tests
in both services.

Fairness research on recommender systems is overwhelmingly user-side; an explicit
supply-side protection is a deliberate design position and a small contribution
of this project.

### 4.3 Explainability as choice architecture

Thaler & Sunstein's (2008) point — that no presentation of a choice is neutral —
applies the moment the platform orders a list. Two commitments follow:

1. **Reasons are computed, not narrated.** Each recommendation returns per-feature
   contributions (standardised value × coefficient) converted to plain language.
   The explanation is arithmetic from the ranking itself, not a plausible story
   written beside it. This is why the ranker remained a linear model when
   gradient boosting was available: the interpretability is the feature.
2. **Verification cannot be out-ranked.** An expired licence is demoted below a
   valid one regardless of predicted match quality. A platform whose premise is
   verification must not let a score override it.

Mathur et al. (2019) documented over a thousand dark-pattern instances across
shopping sites; explainable ranking is a direct structural response.

### 4.4 H3 — did fairness cost accuracy?

**Supported, but the test was weaker than the hypothesis implies, and this should
be stated in the viva rather than discovered there.**

The fairness measures cost little: excluding `nationality` and `continent` still
yields 99.1% accuracy and F1 0.980, and the fair-wage rule is a post-hoc
constraint on a price band, so it cannot degrade classifier metrics at all.

But that is a *weak* test. A strong test of H3 requires a fairness intervention
that genuinely trades against the objective — reweighting, adversarial debiasing,
or an equalised-odds constraint — and measuring the loss. What was actually
measured is that a model which never saw protected attributes still performs
well. That is worth knowing, and it is not the same claim. **H3 is supported for
the mitigations implemented; it is not evidence that fairness is generally free.**

---

## 5. Engineering outcomes

| | Before | After |
|---|---|---|
| Trained models | 2 | **5** |
| Dataset tables used by a model | 7 of 10 | **10 of 10** |
| Genuinely learned models | 1 (scam) | **5** |
| Baselines reported | 1 | **12** across five tasks |
| analytics-engine tests | 4 | **14** |
| core-engine tests | 21 | **26** |

Previously the recommender and guide ranker were hand-weighted scores with no
fitted parameters — they could not be wrong in any measurable way, which is also
to say they could not be right. Both are now learned and evaluated.

**Newly used data.** `tourist_arrivals.csv` (60,000 rows) now drives the
forecaster; `recommendation_interactions.csv` guide ratings now drive the guide
model; `gamification_log.csv` informs segment badge affinity.

---

## 6. Threats to validity

**Synthetic data (most serious).** Every result describes a generated world with
correlations chosen by its author. The pipeline is demonstrably correct and the
relative comparisons are sound, but no number here predicts real-world accuracy.
The clearest evidence of this limit is §2.1: half the relationships the dataset
documentation advertises are absent from the data. A model can only find what the
generator put there.

**Structural ceiling on recommender metrics.** 26 treks behind 2,000 route rows
caps route-level precision independently of model quality. Concept-level metrics
mitigate but do not remove this.

**Short forecasting series.** 48 monthly observations, of which 12 are a COVID
anomaly. §3.4 shows model selection does not replicate across years.

**Small guide-rating sample.** 4,255 rated pairs, 984 in the test year. The 4.8%
improvement is modest relative to that sample size.

**Weak H3 test.** §4.4 — no accuracy-trading fairness intervention was applied.

**Offline evaluation only.** All ranking results are offline. No user ever saw a
recommendation and acted on it, and offline ranking gains are known to transfer
imperfectly to online behaviour.

**Test coverage improved but not comprehensive.** 40 automated tests across both
services, concentrated on inference and API contracts rather than training code.

---

## 7. What was tried and rejected

Recording these matters: they are the difference between "we chose a simple
model" and "we found out which models this data supports."

| Approach | Why rejected |
|---|---|
| Matrix factorisation / item-item CF | Density 0.001, 1.15 positives per user; region history predicts *worse* than the popular-region baseline (23.3% vs 36.9%) |
| Popularity blended into the learned score | Measured: reduced concept HR@10 from 0.0745 to 0.0687–0.0735 at every blend weight tried |
| Gradient boosting for the recommender | Marginally worse than logistic regression (HR@10 0.0131 vs 0.0135) and forfeits readable coefficients |
| Gradient boosting for guide ratings | Overfits 3,271 training rows — RMSE 0.692 vs 0.655 for Ridge |
| Damped-growth forecast with tuned φ | Validation selected φ = 0.25 → 24.3% test MAPE; the parameter-free log-trend achieved 17.2% |
| Full trek-level de-duplication | Costs 38% of the lift (HR@10 0.0138 → 0.0086) |
| `nationality` / `continent` as scam features | Excluded on principle before any measurement |
| `overcharge_ratio` as a scam feature | Deterministic function of the label — meaningless perfect score |

---

## 8. Conclusions for the thesis

1. **Personalisation beats popularity, and the margin is honest.** 1.63×
   hit-rate@10. The absolute numbers are small and the reason is documented.
2. **Learning weights beats setting them — demonstrably.** Given the same
   thirteen features, the learned model discarded the 40% of scoring weight the
   hand-tuned version spent on signals that do not exist in the data.
3. **Risk scoring transfers to this setting better than personalisation does.**
   99.1% accuracy, holding at 0.958 F1 on unseen service/region cells. Features
   built on structured reference data outperform features built on behavioural
   history the market has not yet produced — the practically useful finding for a
   pre-launch platform.
4. **The fairness disparity is in the market, not the model.** Flag rates track
   actual overcharge rates to within 0.006 per group; equalising them would
   under-protect the most-targeted tourists. A direct instance of Chouldechova
   (2017).
5. **Supply-side fairness is implementable, not merely assertable.** The
   below-fair-wage flag exists in code, in two services, with tests.
6. **Negative results are part of the contribution.** Absent preference signals,
   CF-hostile sparsity, a cloned catalog, unstable forecast selection, structureless
   segments, and an honestly weak H3 test.

---

## References

Adomavicius, G. & Tuzhilin, A. (2005) 'Toward the next generation of recommender
systems', *IEEE TKDE*, 17(6), pp. 734–749.

Akerlof, G. (1970) 'The market for "lemons"', *Quarterly Journal of Economics*,
84(3), pp. 488–500.

Chouldechova, A. (2017) 'Fair prediction with disparate impact: a study of bias
in recidivism prediction instruments', *Big Data*, 5(2), pp. 153–163.

Cremonesi, P., Koren, Y. & Turrin, R. (2010) 'Performance of recommender
algorithms on top-N recommendation tasks', *RecSys '10*, pp. 39–46.

Ferrari Dacrema, M., Cremonesi, P. & Jannach, D. (2019) 'Are we really making
much progress? A worrying analysis of recent neural recommendation approaches',
*RecSys '19*, pp. 101–109. (Best Long Paper.)

Hyndman, R.J. & Athanasopoulos, G. (2021) *Forecasting: Principles and Practice*.
3rd edn. Melbourne: OTexts.

Lika, B., Kolomvatsos, K. & Hadjiefthymiades, S. (2014) 'Facing the cold start
problem in recommender systems', *Expert Systems with Applications*, 41(4),
pp. 2065–2073.

Mathur, A. et al. (2019) 'Dark patterns at scale', *Proceedings of the ACM on
Human-Computer Interaction*, 3(CSCW), pp. 1–32.

Ott, M., Choi, Y., Cardie, C. & Hancock, J. (2011) 'Finding deceptive opinion
spam by any stretch of the imagination', *ACL '11*, pp. 309–319.

Simon, H. (1955) 'A behavioral model of rational choice', *Quarterly Journal of
Economics*, 69(1), pp. 99–118.

Thaler, R. & Sunstein, C. (2008) *Nudge*. New Haven: Yale University Press.
