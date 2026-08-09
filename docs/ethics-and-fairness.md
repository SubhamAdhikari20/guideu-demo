# Ethics, Privacy & Fairness

GuideU's proposal commits to responsible, privacy-aware, fairness-aware AI. This
document records how that commitment is implemented, mapped to the dataset's
**Area 6** (`Travel Planning/regulatory_framework.md`). Measured results live in
[RESEARCH_FINDINGS.md](RESEARCH_FINDINGS.md) §4.

## Privacy by design
- **Data minimisation** — the API collects only what a workflow needs; profile
  fields (passport, citizenship) are optional and indexed but never returned in
  list endpoints.
- **No fake credentials** — synthetic tourists are reference rows, not login
  accounts (ADR-0004).
- **Consent hooks** — `accounts` exposes a `data_consent` flag and the analytics
  ingest respects an opt-out; event logging is pseudonymous (user id, not PII).
- **Secrets** — sourced from environment only; `.env` is git-ignored;
  `prod` settings fail fast if `DJANGO_SECRET_KEY` is unset.
- **Synthetic training data as an ethical choice** — the alternative, scraping
  real guide profiles and reviews, would process real people's identities and
  livelihoods without consent. Synthetic data costs external validity; that is
  the price paid, and it is reported rather than hidden.

## Fairness: the scam model must not discriminate

The dataset intentionally simulates real-world tourist-price discrimination —
tourists from Europe / North America / Oceania are quoted systematically higher
prices. A naive classifier could learn "European ⇒ flag," laundering
discrimination into automation.

**Mitigations implemented in `analytics-engine`:**

1. **Protected attributes excluded** from the feature set. `nationality` and
   `continent` are never model inputs; they appear only in the audit. The model
   sees `service_type`, `region`, `season` and the quoted price — what the app
   knows when a tourist types in a number.
2. **Leaky features excluded too.** `overcharge_ratio` and `benchmark_price_npr`
   are a deterministic function of the label, so they are withheld: the model has
   to learn the price band for a cell and judge the quote against it.
3. **Fairness audit after every training run** (`evaluation/fairness.py`) —
   flag-rate and ROC-AUC per continent, with a 0.15 flag-rate disparity gate.
4. **Explainability** — every scam score returns the benchmark, the ratio and the
   reasoning, so a moderator can audit any individual decision.

### The measured result, and how to read it

The audit reports a flag-rate disparity of **0.1615**, which **exceeds the gate**
— so the gate correctly routes the model to review rather than silent deployment.

| Continent | n | Model flag rate | Actual rate |
|---|---|---|---|
| East Asia | 1,874 | 0.154 | 0.154 |
| Europe | 1,939 | 0.306 | 0.302 |
| Latin America | 139 | 0.180 | 0.180 |
| Middle East | 150 | 0.153 | 0.147 |
| North America | 826 | 0.315 | 0.320 |
| Oceania | 387 | 0.305 | 0.308 |
| South Asia | 3,227 | 0.162 | 0.162 |

The model's flag rate tracks each group's **actual** overcharge rate to within
0.006 everywhere. European, North American and Oceanian tourists genuinely are
overcharged more often in this data, so a fair overcharge detector *should* flag
their quotes more often; a detector tuned to equalise flag rates would
systematically under-protect the tourists being targeted most.

This is a textbook instance of Chouldechova's (2017) impossibility result: when
base rates differ between groups, calibration and error-rate balance cannot both
hold, and choosing between them is a normative decision, not a technical one.

**GuideU's stated position:** calibrate to the world, never take nationality as
an input, and make the resulting disparity inspectable rather than tuning it
away. The mitigation is structural — exclude protected attributes, always return
the evidence, and escalate to a human when the gate trips.

## Recommendations: traceable, not a black box

Ranking is choice architecture (Thaler & Sunstein, 2008): whatever sits at the
top of a list changes what people book.

- The ranker is a **linear model by choice**. Gradient boosting was available and
  performed no better (hit-rate@10 0.0131 vs 0.0135), so the interpretable model
  was kept — the interpretability is the feature, not a compromise.
- Every recommendation returns **per-feature contributions** (standardised value ×
  coefficient) rendered as plain-language reasons. The explanation is arithmetic
  taken from the ranking itself, not a narrative written alongside it.
- The mobile app surfaces the top reason on each recommendation card, so "why am
  I seeing this?" is answerable in the interface, not just in the API.

## Verification cannot be out-ranked

An expired licence is demoted below a valid one regardless of predicted match
quality, and a guide who does not cover the requested region or speak the
requested language is filtered out rather than scored. A platform whose premise
is verification must not allow a model score to override verification status.

## Worker fairness: the below-fair-wage flag

Price transparency has an asymmetric failure mode. Publishing a fair range helps
a tourist detect an overcharge — and equally helps them anchor every negotiation
at the bottom of that range. For guides and porters, that floor is a daily wage.
Left unaddressed, the platform's own transparency becomes downward wage pressure.

**Implemented** (`inference/pricing.wage_check`, mirrored in
`core-engine/src/trust/services.py`):

- A quote below **95% of the fair floor** for a **labour** service (Licensed
  Guide, Porter) raises `below_fair_wage`.
- The mobile app renders it as its own outcome — its own colour, icon and
  headline — never as a good deal:

  > *"This is 45.5% below the fair rate for a licensed guide. Paying under the
  > fair range pushes licensed workers out of the market — please consider the
  > fair rate of 4,740 NPR."*

- Permits, meals and transport are **exempt**. A cheap permit is a fee; a cheap
  guide is an underpaid person.
- The rule is enforced independently in both services, so it survives an ML
  outage, and is covered by tests in both.

Fairness work on recommender systems is overwhelmingly user-side. An explicit
supply-side protection is a deliberate design position of this project.

## What is not claimed

- The scam model **does not detect intent**. It scores price patterns resembling
  previously-labelled overcharging — a statistical association, not a judgement
  about a person, and the UI wording reflects that.
- The fairness measures were **not tested against a real accuracy trade-off**.
  Excluding protected attributes cost little (99.1% accuracy retained), but no
  intervention that genuinely trades against the objective — reweighting,
  adversarial debiasing, equalised odds — was applied. H3 is supported for the
  mitigations built; it is not evidence that fairness is generally free.
- Results come from **synthetic data**, so none of them establishes real-world
  fairness in deployment.
