# GuideU's five models — the plain-English version

No jargon. One page per model: what it does, how it works, how well it works, and
what it cannot do. The technical detail lives in [ml.md](ml.md).

All five are trained on the **Travel Planning** dataset — 500,000 synthetic rows
across ten linked tables. All five learn from 2021–2023 and are tested on 2024,
so they are always judged on data from *after* the data they learned from.

---

## 1. The trek recommender

**What it does.** A traveller opens the app and sees "Recommended for you" — a
shortlist of treks picked for them out of 2,000 in the catalog.

**How it works.** The model looks at pairs: *this traveller* and *this trek*. It
was shown 11,900 real choices from the dataset ("this person booked that trek")
plus a set of treks they did not book, and it learned what separates the two.

The interesting part is what it learned. It was offered thirteen clues — the
traveller's culture, adventure and nature scores, their risk appetite and price
sensitivity, and the trek's difficulty, cost, altitude, length and popularity. It
decided that **one clue does almost all the work**: how closely the trek's
difficulty matches the traveller's appetite for adventure. Everything else it
pushed to near-zero.

That matters, because the old version of this feature had its weights set by
hand, and it spent 40% of its scoring on budget and season — two things that turn
out to carry no signal in this data at all. Letting the model choose the weights
found that out automatically.

**How well it works.** Compared with simply showing everyone the most popular
treks, it is **1.63× better** at putting a trek the traveller actually chose in
the top 10.

**What it cannot do.** The absolute hit rate is low — about 1.4%. With 2,000
treks and most travellers having booked only one, that is the ceiling this data
allows. It also cannot tell you what someone will *enjoy*; it knows what
attributes went with past choices.

**One extra touch.** The catalog secretly contains only 26 real treks, each sold
under about 15 different names. Left alone, the shortlist filled up with four
versions of the same trail, so the app now allows at most three variants of any
one trek per list.

---

## 2. The scam detector

**What it does.** A traveller is quoted a price — 12,000 rupees for a guide, say
— types it in, and gets back "this looks fair" or "this looks overpriced", with
the reason.

**How it works.** It was trained on 35,000 reported quotes, each labelled fair or
overcharged. It sees only four things: what the service is, which region, which
season, and the price. That is deliberate — it is exactly what the app knows when
a traveller types a number in.

Two things were **kept away from it on purpose**:

- *The answer.* The dataset works out "overcharged" by dividing the quote by the
  official benchmark. Handing the model that division would be handing it the
  answer key — it would score perfectly and have learned nothing.
- *Nationality.* The dataset deliberately simulates the real pattern where
  Western tourists get quoted more. A model allowed to see nationality would
  learn to price-profile people. It never sees it.

**How well it works.** **99.1% accurate**, F1 score 0.980. More importantly, when
tested on 60 service-and-region combinations it had *never seen before*, it still
scored 0.958 — so it learned how prices behave, not a lookup table.

**What it cannot do.** It cannot prove anyone intended to cheat anybody. It
recognises price patterns that resemble previously-labelled overcharging. That is
a statistical association, not a judgement about a person, and the app words it
that way.

**The fairness finding.** The model flags European and North American travellers'
quotes about twice as often as East and South Asian ones. That looks alarming
until you check the actual overcharge rates — they match, to within half a
percentage point. Those travellers genuinely are overcharged more often in this
data, so a detector that *didn't* flag them more would be failing them. The
imbalance is in the world being modelled, not in the model.

---

## 3. The guide matcher

**What it does.** Ranks verified guides for a particular traveller.

**How it works.** It learned from 4,255 real ratings — "this traveller gave that
guide 4 out of 5" — and predicts the score *this* traveller would give *this*
guide, from the guide's credentials and the traveller's profile. Then it sorts by
that prediction.

**How well it works.** Its error is 0.655 stars, against 0.688 for guessing the
average every time — a **4.8% improvement**. Small, but genuine.

The more useful finding is the comparison nobody usually runs. The obvious
no-model approach is "just show the highest-rated guides." That scores **0.705 —
worse than guessing the average.** A guide's overall rating turns out to be a
poor guide to how one particular traveller will get on with them. That is the
whole argument for matching rather than sorting by stars.

**Two rules sit outside the model.** A guide who doesn't cover your region or
speak your language is filtered out rather than scored — that is a requirement,
not a preference. And an expired licence is always pushed below a valid one, no
matter how good the prediction. A verification platform that ranked an expired
licence first would be defeating itself.

---

## 4. The demand forecaster

**What it does.** Predicts how many tourists will arrive in Nepal each month, so
admins can plan guide capacity and travellers can be told which months are busy.

**How it works.** Four years of arrivals (2021–2024) are boiled down to a
48-month series. The model fits a trend line and twelve monthly adjustments —
but on the *logarithm* of arrivals, so each month is treated as a percentage of
the year's level rather than a fixed headcount. That is the right shape for a
growing market: October is roughly 1.5× an average month whether the year totals
100,000 or 1.5 million.

It also ignores 2021 on purpose. Nepal received 100,000 tourists that year and
1.5 million in 2024 — 2021 is a COVID anomaly and fitting a line through it
bends everything.

**How well it works.** Average error **17.2%**, against 38.6% for "same as last
year". Roughly half the error.

**What it cannot do — and this one is worth reading.** There are only three years
of usable history, which means only two observations of year-on-year growth. When
the same models were tested on 2023 instead of 2024, **the ranking completely
reversed** — the simple "same as last year" method won and this model was
catastrophically wrong.

So the honest statement is: this model wins on the real held-out year, but three
years of a post-pandemic recovery is not enough data to be confident it will keep
winning. That is why every forecast is shown as a *range*, never a single number.

---

## 5. Traveller segments

**What it does.** A brand-new user has no history, so the recommender has nothing
to work with. Segments give them a reasonable starting profile — better than
assuming they are perfectly average.

**How it works.** K-means sorts the 40,000 traveller profiles into four groups by
their five preference scores. The four that emerged:

| Segment | Roughly | Size |
|---|---|---|
| 0 | Budget-conscious, nature-loving | 10,276 |
| 1 | Risk-tolerant | 10,047 |
| 2 | City-leaning, budget-conscious | 9,503 |
| 3 | Comfort-spending, safety-first | 10,174 |

**How well it works — and here the honest answer is "not very".** The standard
measure of whether clusters are real (silhouette score) comes out at about 0.13
no matter whether you ask for 2 groups or 8. That means **there are no natural
groups**. The preference scores form one diffuse cloud; the generator drew them
close to independently. Cutting it into four is drawing lines on fog.

They are still slightly useful. Members of different segments do book measurably
different treks (statistically that result is beyond doubt, p ≈ 10⁻¹³) — but the
difference between the most and least adventurous segment is only about a fifth
of a standard deviation. Real, but small.

**So they are used as a cold-start default and nothing more.** They are not shown
to users as their "travel personality", because the data does not support that
claim.

---

## The fair-wage rule (not a model, but the point of the project)

Every other feature here protects the tourist. This one protects the guide.

Publishing a fair price range helps a traveller spot a rip-off. It just as
effectively helps them open every negotiation at the bottom of that range — and
for a guide or a porter, the bottom of the range is a day's wage.

So the price checker works in **both directions**. Quote too high and it warns
about an overcharge. Quote too low for a guide or porter and it says so plainly:
*"This is 45% below the fair rate for a licensed guide. Paying under the fair
range pushes licensed workers out of the market."* The app shows that as its own
outcome — not as a good deal.

Permits, meals and bus tickets are exempt. A cheap permit is a cheap fee; a cheap
guide is an underpaid person.

---

## Retraining everything

```bash
cd services/analytics-engine
python -m training.run_all --report artifacts/training_report.json
```

Roughly two minutes. It prints every model's score next to its baselines, so it
is always visible whether a model is earning its place.
