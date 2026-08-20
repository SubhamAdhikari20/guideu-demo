"""Exploratory data analysis and results charts for the GuideU thesis.

Reads the Travel Planning dataset and the training report produced by
``python -m training.run_all`` in services/analytics-engine, and writes the
charts used in the Findings chapter.

Run:
    python scripts/eda_findings.py

Everything it prints is also written to stats.json next to the charts, so the
numbers quoted in the report can be checked against the numbers on the charts.
"""
from __future__ import annotations

import json
import os
import re
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = REPO_ROOT.parent
DATA = Path(os.environ.get("GUIDEU_DATASET_DIR", WORKSPACE_ROOT / "Travel Planning"))
REPORT = Path(os.environ.get(
    "GUIDEU_TRAINING_REPORT",
    REPO_ROOT / "services" / "analytics-engine" / "artifacts" / "training_report.json",
))
OUT = Path(os.environ.get("GUIDEU_EDA_OUTPUT", WORKSPACE_ROOT / "Thesis_EDA_Charts"))
OUT.mkdir(parents=True, exist_ok=True)

# Categorical slots, in fixed order. Validated against a white page surface:
# worst adjacent CVD dE 9.1, worst adjacent normal-vision dE 19.6.
C = {
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "magenta": "#e87ba4",
    "green": "#008300",
    "violet": "#4a3aa7",
    "red": "#e34948",
}
SERIES = [C["blue"], C["orange"], C["aqua"], C["yellow"],
          C["magenta"], C["green"], C["violet"], C["red"]]
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
GOOD, WARN, CRIT = "#0ca30c", "#fab219", "#d03b3b"

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#ffffff"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "600",
    "axes.titlecolor": INK,
    "axes.labelsize": 11,
    "axes.labelcolor": INK2,
    "axes.edgecolor": AXIS,
    "axes.linewidth": 1.0,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.9,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelcolor": INK2,
    "ytick.labelcolor": INK2,
    "legend.frameon": False,
    "legend.fontsize": 10,
    "lines.linewidth": 2.0,
    "lines.markersize": 8,
    "figure.dpi": 150,
})

STATS: dict = {}


def finish(fig, ax_or_axes, name: str, title: str, sub: str = "", source: str = "") -> None:
    """Common chrome, then save.

    Title, subtitle and source sit outside the plotting box and are spaced in
    inches rather than figure fractions, so short figures do not stack their
    own headings on top of each other.
    """
    axes = np.atleast_1d(ax_or_axes).ravel()
    for ax in axes:
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.spines["left"].set_color(AXIS)
        ax.spines["bottom"].set_color(AXIS)

    h = fig.get_figheight()
    if sub:
        fig.text(0.0, 1.0 + 0.07 / h, sub, ha="left", va="bottom",
                 fontsize=11, color=INK2)
        fig.text(0.0, 1.0 + 0.36 / h, title, ha="left", va="bottom",
                 fontsize=15, fontweight="600", color=INK)
    else:
        fig.text(0.0, 1.0 + 0.07 / h, title, ha="left", va="bottom",
                 fontsize=15, fontweight="600", color=INK)
    if source:
        # Sit the source line below whatever is lowest in the figure, which is
        # usually a legend anchored under the axes rather than the axes itself.
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        inv = fig.transFigure.inverted()
        lowest = 0.0
        for ax in axes:
            legend = ax.get_legend()
            if legend is not None:
                lowest = min(lowest, legend.get_window_extent(renderer)
                             .transformed(inv).y0)
            lowest = min(lowest, ax.get_tightbbox(renderer).transformed(inv).y0)
        fig.text(0.0, lowest - 0.16 / h, source, ha="left", va="top",
                 fontsize=9, color=MUTED)

    fig.savefig(OUT / name, bbox_inches="tight", pad_inches=0.30)
    plt.close(fig)
    print(f"  {name}")


def barlabels(ax, bars, fmt="{:,.0f}", pad=3, colour=INK, size=10, horizontal=False):
    for b in bars:
        if horizontal:
            v = b.get_width()
            ax.annotate(fmt.format(v), (v, b.get_y() + b.get_height() / 2),
                        xytext=(pad, 0), textcoords="offset points",
                        va="center", ha="left", fontsize=size, color=colour)
        else:
            v = b.get_height()
            ax.annotate(fmt.format(v), (b.get_x() + b.get_width() / 2, v),
                        xytext=(0, pad), textcoords="offset points",
                        ha="center", va="bottom", fontsize=size, color=colour)


def thousands(ax, axis="y"):
    f = FuncFormatter(lambda v, _: f"{v:,.0f}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(f)


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
print("Loading dataset ...")
tourists = pd.read_csv(DATA / "tourists.csv")
routes = pd.read_csv(DATA / "trekking_routes.csv")
guides = pd.read_csv(DATA / "verified_guides.csv")
bookings = pd.read_csv(DATA / "bookings.csv")
interactions = pd.read_csv(DATA / "recommendation_interactions.csv")
scams = pd.read_csv(DATA / "scam_reports.csv")
prices = pd.read_csv(DATA / "pricing_benchmarks.csv")
arrivals = pd.read_csv(DATA / "tourist_arrivals.csv")
events = pd.read_csv(DATA / "cultural_events.csv")
gamification = pd.read_csv(DATA / "gamification_log.csv")

TABLES = {
    "recommendation_interactions": interactions, "bookings": bookings,
    "pricing_benchmarks": prices, "tourist_arrivals": arrivals,
    "tourists": tourists, "scam_reports": scams,
    "gamification_log": gamification, "verified_guides": guides,
    "cultural_events": events, "trekking_routes": routes,
}
STATS["table_rows"] = {k: int(len(v)) for k, v in TABLES.items()}
STATS["total_rows"] = int(sum(len(v) for v in TABLES.values()))

# The pipeline's own definitions, copied so the charts match the models.
POSITIVE = ["Book", "Complete"]
VARIANT_SUFFIX = r"\s*\([^)]*\)\s*$"

route_inter = interactions[interactions["item_type"] == "Route"].copy()
route_inter["date"] = pd.to_datetime(route_inter["interaction_date"])
positives = route_inter[route_inter["interaction_type"].isin(POSITIVE)].copy()
routes["trek"] = routes["route_name"].str.replace(VARIANT_SUFFIX, "", regex=True)

bookings["booking_date"] = pd.to_datetime(bookings["booking_date"])
scams["reported_date"] = pd.to_datetime(scams["reported_date"])

train_report = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}


# ===========================================================================
# PART A - what the dataset is
# ===========================================================================
print("\nPart A: dataset description")

# A1 - table sizes
fig, ax = plt.subplots(figsize=(9.2, 5.0))
s = pd.Series(STATS["table_rows"]).sort_values()
bars = ax.barh(s.index.str.replace("_", " "), s.values, color=SEQ[3], height=0.62)
barlabels(ax, bars, horizontal=True)
ax.set_xlim(0, s.max() * 1.17)
ax.set_xlabel("Rows")
ax.grid(axis="y", visible=False)
thousands(ax, "x")
finish(fig, ax, "eda01_table_sizes.png",
       "Ten linked tables, about 500,000 rows",
       f"{STATS['total_rows']:,} rows in total. Every table now feeds a model or the profiling behind one.",
       "Source: Travel Planning dataset, seed 20240519")

# A2 - missing values
miss = {}
for name, df in TABLES.items():
    for col in df.columns:
        pct = df[col].isna().mean() * 100
        if pct > 0:
            miss[f"{name}.{col}"] = pct
STATS["missing_columns"] = {k: round(v, 2) for k, v in miss.items()}
fig, ax = plt.subplots(figsize=(9.2, 3.4))
m = pd.Series(miss).sort_values()
bars = ax.barh(m.index, m.values, color=C["yellow"], height=0.55)
barlabels(ax, bars, fmt="{:.1f}%", horizontal=True)
ax.set_xlim(0, max(m.max() * 1.25, 12))
ax.set_xlabel("Missing values")
ax.xaxis.set_major_formatter(PercentFormatter())
ax.grid(axis="y", visible=False)
finish(fig, ax, "eda02_missing_values.png",
       "Only three columns have missing values",
       "Everything else is complete, so cleaning was mostly type fixing and date parsing rather than imputation.",
       "Source: Travel Planning dataset")

# A3 - traveller demographics
fig, axes = plt.subplots(2, 2, figsize=(9.6, 6.6))
panels = [
    ("continent", "Continent", C["blue"]),
    ("age_group", "Age group", C["aqua"]),
    ("budget_band", "Budget band", C["violet"]),
    ("travel_style", "Travel style", C["orange"]),
]
for ax, (col, label, colour) in zip(axes.ravel(), panels):
    vc = tourists[col].value_counts().sort_values()
    bars = ax.barh(vc.index, vc.values, color=colour, height=0.6)
    barlabels(ax, bars, horizontal=True, size=9)
    ax.set_xlim(0, vc.max() * 1.24)
    ax.set_title(label, fontsize=12, loc="left", pad=6)
    ax.grid(axis="y", visible=False)
    thousands(ax, "x")
fig.tight_layout()
finish(fig, axes, "eda03_traveller_profile.png",
       "Who is in the 40,000 traveller profiles",
       "Coverage is broad and fairly even, which is useful for description but means few sharp subgroups to learn from.",
       "Source: tourists.csv")

# A4 - preference score distributions
prefs = ["pref_culture_score", "pref_adventure_score", "pref_nature_score",
         "risk_tolerance", "price_sensitivity"]
fig, ax = plt.subplots(figsize=(9.2, 4.6))
for k, (col, colour) in enumerate(zip(prefs, SERIES)):
    ax.hist(tourists[col], bins=40, histtype="step", linewidth=2.0,
            color=colour, label=col.replace("pref_", "").replace("_score", "").replace("_", " "))
ax.set_xlabel("Score")
ax.set_ylabel("Travellers")
ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.16))
thousands(ax)
finish(fig, ax, "eda04_preference_distributions.png",
       "The five preference scores are broad and almost independent",
       "No natural grouping is visible in any single score, which is the first hint that segmentation will struggle.",
       "Source: tourists.csv")


# ===========================================================================
# PART B - signal search
# ===========================================================================
print("\nPart B: looking for signal")

# Join positives to the traveller profile and route attributes
pos_join = (positives
            .merge(tourists[["tourist_id", "pref_adventure_score", "pref_culture_score",
                             "pref_nature_score", "budget_band", "fitness_level",
                             "experience_level", "price_sensitivity"]],
                   on="tourist_id", how="left")
            .merge(routes[["route_id", "difficulty_level", "estimated_cost_usd",
                           "max_altitude_m", "region", "duration_days"]],
                   left_on="item_id", right_on="route_id", how="inner"))
STATS["positive_route_interactions"] = int(len(positives))
STATS["joined_positive_rows"] = int(len(pos_join))

# B1 - the one real signal
pos_join["adv_q"] = pd.qcut(pos_join["pref_adventure_score"], 5, labels=[1, 2, 3, 4, 5])
q = pos_join.groupby("adv_q", observed=True).agg(
    n=("route_id", "size"),
    difficulty=("difficulty_level", "mean"),
    cost=("estimated_cost_usd", "mean"),
    altitude=("max_altitude_m", "mean"),
).reset_index()
STATS["adventure_quintiles"] = q.round(3).to_dict("records")

fig, axes = plt.subplots(1, 3, figsize=(9.8, 3.9))
for ax, (col, label, fmt, colour) in zip(axes, [
        ("difficulty", "Mean difficulty (1 to 4)", "{:.2f}", C["blue"]),
        ("cost", "Mean cost (USD)", "{:,.0f}", C["aqua"]),
        ("altitude", "Mean max altitude (m)", "{:,.0f}", C["violet"])]):
    bars = ax.bar(q["adv_q"].astype(str), q[col], color=colour, width=0.62)
    barlabels(ax, bars, fmt=fmt, size=9)
    ax.set_title(label, fontsize=11.5, loc="left", pad=6)
    ax.set_xlabel("Adventure preference quintile")
    ax.set_ylim(0, q[col].max() * 1.20)
    ax.grid(axis="x", visible=False)
fig.tight_layout()
finish(fig, axes, "eda05_adventure_signal.png",
       "The one preference that actually predicts what people book",
       "Mean booked difficulty rises steadily from quintile 1 to quintile 5. Cost and altitude follow because both track difficulty.",
       f"Source: {len(pos_join):,} booked or completed route interactions")

# B2 - the relationships that are not there
flat = {}
b = pos_join.groupby("budget_band", observed=True)["estimated_cost_usd"].mean()
flat["Budget band to route cost (USD)"] = (b.index.tolist(), b.values.tolist(), "{:,.0f}")
pos_join["nat_q"] = pd.qcut(pos_join["pref_nature_score"], 5, labels=[1, 2, 3, 4, 5])
n = pos_join.groupby("nat_q", observed=True)["max_altitude_m"].mean()
flat["Nature score to altitude (m)"] = ([str(x) for x in n.index], n.values.tolist(), "{:,.0f}")
f = pos_join.dropna(subset=["fitness_level"]).groupby("fitness_level", observed=True)["difficulty_level"].mean()
flat["Fitness level to difficulty"] = (f.index.tolist(), f.values.tolist(), "{:.3f}")
e = pos_join.groupby("experience_level", observed=True)["difficulty_level"].mean()
flat["Experience level to difficulty"] = (e.index.tolist(), e.values.tolist(), "{:.3f}")
STATS["flat_relationships"] = {k: dict(zip(v[0], [round(x, 3) for x in v[1]]))
                               for k, v in flat.items()}

fig, axes = plt.subplots(1, 4, figsize=(10.2, 3.8))
for ax, (title, (labels, vals, fmt)) in zip(axes, flat.items()):
    bars = ax.bar([str(x) for x in labels], vals, color=C["orange"], width=0.6)
    barlabels(ax, bars, fmt=fmt, size=8.5)
    lo, hi = min(vals), max(vals)
    pad = max((hi - lo) * 2.2, hi * 0.06)
    ax.set_ylim(max(0, lo - pad), hi + pad)
    ax.set_title(title, fontsize=10.5, loc="left", pad=6)
    ax.tick_params(axis="x", labelrotation=30, labelsize=8.5)
    ax.grid(axis="x", visible=False)
fig.tight_layout()
finish(fig, axes, "eda06_flat_relationships.png",
       "Four relationships the documentation promised, and none of them is there",
       "The y axis on each panel is zoomed right in. Even at that zoom the bars are almost level, so these features carry no usable signal.",
       "Source: booked or completed route interactions joined to traveller profiles")

# B3 - correlation heatmap
num = pos_join[["pref_adventure_score", "pref_culture_score", "pref_nature_score",
                "price_sensitivity", "difficulty_level", "estimated_cost_usd",
                "max_altitude_m", "duration_days"]].copy()
num.columns = ["adventure", "culture", "nature", "price sens.",
               "difficulty", "cost", "altitude", "duration"]
corr = num.corr()
STATS["corr_adventure_difficulty"] = round(float(corr.loc["adventure", "difficulty"]), 4)
fig, ax = plt.subplots(figsize=(6.8, 5.6))
im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(corr)), corr.columns, rotation=45, ha="right")
ax.set_yticks(range(len(corr)), corr.columns)
for r in range(len(corr)):
    for c in range(len(corr)):
        v = corr.iloc[r, c]
        ax.text(c, r, f"{v:.2f}", ha="center", va="center", fontsize=8.5,
                color="#ffffff" if abs(v) > 0.55 else INK)
ax.grid(False)
fig.colorbar(im, ax=ax, shrink=0.72, label="Pearson r")
finish(fig, ax, "eda07_correlation.png",
       "Only one traveller feature correlates with anything booked",
       "Adventure preference against booked difficulty is the single off-diagonal pair worth modelling.",
       "Source: booked or completed route interactions")

# B4 - sparsity
per_user = positives.groupby("tourist_id").size()
users_with_inter = route_inter["tourist_id"].nunique()
STATS["users_with_route_interactions"] = int(users_with_inter)
STATS["users_with_positive"] = int(per_user.size)
STATS["mean_positives_per_user"] = round(float(per_user.mean()), 3)
STATS["matrix_density"] = round(float(len(positives) / (per_user.size * len(routes))), 6)
STATS["users_more_than_one"] = int((per_user > 1).sum())
STATS["users_more_than_one_pct"] = round(float((per_user > 1).mean() * 100), 1)

fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.0),
                         gridspec_kw={"width_ratios": [1.05, 1]})
ax = axes[0]
vc = per_user.value_counts().sort_index()
vc = vc[vc.index <= 6]
bars = ax.bar(vc.index.astype(str), vc.values, color=C["blue"], width=0.62)
barlabels(ax, bars, size=9)
ax.set_xlabel("Booked or completed routes per traveller")
ax.set_ylabel("Travellers")
ax.set_ylim(0, vc.max() * 1.18)
ax.grid(axis="x", visible=False)
thousands(ax)

ax = axes[1]
ax.axis("off")
lines = [
    ("Travellers with any route activity", f"{users_with_inter:,}"),
    ("Travellers with a positive", f"{per_user.size:,}"),
    ("Route items", f"{len(routes):,}"),
    ("Mean positives per traveller", f"{per_user.mean():.2f}"),
    ("Matrix density", f"{STATS['matrix_density']:.5f}"),
    ("More than one positive", f"{STATS['users_more_than_one']:,}  ({STATS['users_more_than_one_pct']}%)"),
]
for k, (lab, val) in enumerate(lines):
    yy = 0.90 - k * 0.155
    ax.text(0.02, yy, lab, fontsize=10.5, color=INK2, va="center")
    ax.text(0.98, yy, val, fontsize=12.5, color=INK, va="center", ha="right",
            fontweight="600")
    ax.plot([0.02, 0.98], [yy - 0.058, yy - 0.058], color=GRID, lw=1)
finish(fig, axes, "eda08_sparsity.png",
       "Almost nobody books twice, so there is nothing for collaborative filtering to use",
       "A neighbour based method needs users who overlap on items. At 1.15 positives each, they hardly ever do.",
       "Source: recommendation_interactions.csv, Book and Complete events on routes")

# B5 - catalogue cloning
STATS["route_rows"] = int(routes["route_id"].nunique())
STATS["route_concepts"] = int(routes["route_name"].nunique())
STATS["base_treks"] = int(routes["trek"].nunique())
per_trek = routes.groupby("trek").size().sort_values(ascending=False)
fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2),
                         gridspec_kw={"width_ratios": [0.8, 1.2], "wspace": 0.42})
ax = axes[0]
levels = ["Route\nrows", "Distinct\nnames", "Base\ntreks"]
vals = [STATS["route_rows"], STATS["route_concepts"], STATS["base_treks"]]
bars = ax.bar(levels, vals, color=[SEQ[2], SEQ[4], C["orange"]], width=0.6)
barlabels(ax, bars, size=10)
ax.set_yscale("log")
ax.set_ylabel("Count (log scale)")
ax.set_ylim(10, 5000)
ax.grid(axis="x", visible=False)
ax = axes[1]
top = per_trek.head(12).sort_values()
bars = ax.barh(top.index, top.values, color=SEQ[3], height=0.62)
barlabels(ax, bars, horizontal=True, size=9)
ax.set_xlim(0, top.max() * 1.16)
ax.set_xlabel("Route rows carrying this trek name")
ax.grid(axis="y", visible=False)
finish(fig, axes, "eda09_catalogue_cloning.png",
       "Two thousand route rows are really twenty six treks",
       "Each trek repeats as many packaged variants. A model can pick the right trek and still miss the exact row that was booked.",
       "Source: trekking_routes.csv")


# ===========================================================================
# PART C - price and scam evidence
# ===========================================================================
print("\nPart C: price and risk")

# C1 - overcharge ratio by severity
order = ["Fair", "Mild Overcharge", "Moderate Overcharge", "Severe Overcharge", "Likely Scam"]
present = [s for s in order if s in set(scams["scam_severity"])]
fig, ax = plt.subplots(figsize=(9.2, 4.4))
data = [scams.loc[scams["scam_severity"] == s, "overcharge_ratio"] for s in present]
bp = ax.boxplot(data, tick_labels=[s.replace(" ", "\n") for s in present],
                patch_artist=True, widths=0.5,
                medianprops=dict(color=INK, lw=1.8),
                whiskerprops=dict(color=AXIS), capprops=dict(color=AXIS),
                flierprops=dict(marker=".", markersize=3, markerfacecolor=MUTED,
                                markeredgecolor="none", alpha=0.35))
ramp = [GOOD, "#9acd32", WARN, "#ec835a", CRIT]
for patch, colour in zip(bp["boxes"], ramp[:len(present)]):
    patch.set_facecolor(colour)
    patch.set_alpha(0.85)
    patch.set_edgecolor("none")
ax.axhline(1.25, color=INK, ls="--", lw=1.4)
ax.annotate("flag threshold, ratio 1.25", (0.55, 1.25), xytext=(0, 8),
            textcoords="offset points", fontsize=9.5, color=INK)
ax.set_ylabel("Quoted price / fair benchmark")
ax.grid(axis="x", visible=False)
STATS["overcharge_by_severity"] = {
    s: round(float(scams.loc[scams["scam_severity"] == s, "overcharge_ratio"].median()), 3)
    for s in present}
finish(fig, ax, "eda10_overcharge_ratio.png",
       "Overcharge ratio separates the severity classes cleanly",
       "The classes barely overlap, which is why the label is easy to predict and why the accuracy figure needs a caveat.",
       "Source: scam_reports.csv, 35,000 reports")

# C2 - the label is a step function (leakage evidence)
bins = np.arange(0.6, 2.61, 0.05)
scams["ratio_bin"] = pd.cut(scams["overcharge_ratio"], bins)
rate = scams.groupby("ratio_bin", observed=True)["was_flagged_by_app"].mean()
centres = [iv.mid for iv in rate.index]
fig, ax = plt.subplots(figsize=(9.2, 4.2))
ax.plot(centres, rate.values, color=C["red"], lw=2.4)
ax.fill_between(centres, 0, rate.values, color=C["red"], alpha=0.12)
ax.axvline(1.25, color=INK, ls="--", lw=1.4)
ax.annotate("every quote below 1.25 is unflagged,\nevery quote above 1.30 is flagged",
            (1.32, 0.42), fontsize=10, color=INK)
ax.set_xlabel("Overcharge ratio")
ax.set_ylabel("Share flagged")
ax.yaxis.set_major_formatter(PercentFormatter(1.0))
ax.set_ylim(-0.03, 1.08)
ax.grid(axis="x", visible=False)
finish(fig, ax, "eda11_label_step_function.png",
       "Why the overcharge ratio had to be dropped from the feature set",
       "The label is a step on the ratio. Feeding the ratio back in would have produced a perfect score that means nothing.",
       "Source: scam_reports.csv")

# C3 - fair price spread by service
svc = (prices.groupby("service_type")
       .agg(low=("min_fair_npr", "median"), mid=("fair_price_npr", "median"),
            high=("max_fair_npr", "median"))
       .sort_values("mid"))
fig, ax = plt.subplots(figsize=(9.2, 6.0))
ypos = np.arange(len(svc))
ax.hlines(ypos, svc["low"], svc["high"], color=SEQ[2], lw=6, alpha=0.85)
ax.plot(svc["mid"], ypos, "o", color=SEQ[5], markersize=7, zorder=3)
for y, (lo, mid, hi) in enumerate(svc.itertuples(index=False)):
    ax.annotate(f"{mid:,.0f}", (hi, y), xytext=(8, 0), textcoords="offset points",
                va="center", fontsize=9, color=INK2)
ax.set_yticks(ypos, svc.index)
ax.set_xscale("log")
ax.set_xlabel("Fair price band, NPR (log scale)")
ax.set_xlim(150, svc["high"].max() * 2.6)
ax.grid(axis="y", visible=False)
finish(fig, ax, "eda12_price_bands.png",
       "The reference data a price check is built on",
       "Median fair band per service across all regions and seasons. Labour services sit in the middle of the range.",
       "Source: pricing_benchmarks.csv, 85,000 benchmark rows")

# C4 - overcharge base rate by continent
sc = scams.merge(tourists[["tourist_id", "continent"]], on="tourist_id", how="left")
cont = (sc.groupby("continent")
        .agg(n=("report_id", "size"), rate=("was_flagged_by_app", "mean"))
        .sort_values("rate"))
STATS["overcharge_rate_by_continent"] = {k: round(float(v), 4)
                                         for k, v in cont["rate"].items()}
fig, ax = plt.subplots(figsize=(9.2, 4.2))
bars = ax.barh(cont.index, cont["rate"] * 100, color=SEQ[3], height=0.6)
barlabels(ax, bars, fmt="{:.1f}%", horizontal=True)
ax.set_xlim(0, cont["rate"].max() * 100 * 1.22)
ax.set_xlabel("Share of reported quotes that are above the fair band")
ax.xaxis.set_major_formatter(PercentFormatter())
ax.grid(axis="y", visible=False)
finish(fig, ax, "eda13_overcharge_by_continent.png",
       "Different groups really are quoted differently in this data",
       "This is the base rate difference in the market, before any model sees it. It is what the fairness audit later has to interpret.",
       "Source: scam_reports.csv joined to tourists.csv")


# ===========================================================================
# PART D - demand and supply
# ===========================================================================
print("\nPart D: demand and supply")

# D1 - monthly arrivals
monthly = (arrivals.groupby(["year", "month"])["arrival_count"].sum()
           .reset_index().sort_values(["year", "month"]))
monthly["t"] = pd.to_datetime(dict(year=monthly.year, month=monthly.month, day=1))
STATS["yearly_arrivals"] = {int(y): int(v) for y, v in
                            arrivals.groupby("year")["arrival_count"].sum().items()}
fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.0),
                         gridspec_kw={"width_ratios": [1.5, 1]})
ax = axes[0]
ax.plot(monthly["t"], monthly["arrival_count"], color=C["blue"], lw=2.2)
ax.fill_between(monthly["t"], 0, monthly["arrival_count"], color=C["blue"], alpha=0.10)
ax.set_ylabel("Arrivals per month")
ax.set_xlabel("")
year_starts = monthly.loc[monthly["month"] == 1, "t"]
ax.set_xticks(year_starts, [d.year for d in year_starts])
thousands(ax)
ax.grid(axis="x", visible=False)
ax = axes[1]
season = arrivals.groupby("season")["arrival_count"].sum()
season = season / season.sum()
season = season.sort_values()
bars = ax.barh(season.index, season.values * 100, color=C["aqua"], height=0.58)
barlabels(ax, bars, fmt="{:.0f}%", horizontal=True)
ax.set_xlim(0, season.max() * 100 * 1.25)
ax.set_xlabel("Share of arrivals")
ax.xaxis.set_major_formatter(PercentFormatter())
ax.grid(axis="y", visible=False)
finish(fig, axes, "eda14_arrivals.png",
       "Forty eight months of arrivals, and only two clean growth observations",
       "The series climbs steeply out of the pandemic and peaks each autumn. Three of the four years are recovery years.",
       "Source: tourist_arrivals.csv, 60,000 cohort rows")

# D2 - booking concentration
reg = bookings["region"].value_counts()
share = (reg / reg.sum()).sort_values()
STATS["top2_region_share"] = round(float(share.tail(2).sum()), 4)
fig, ax = plt.subplots(figsize=(9.2, 4.6))
colours = [C["orange"] if v >= share.iloc[-2] else SEQ[3] for v in share.values]
bars = ax.barh(share.index, share.values * 100, color=colours, height=0.6)
barlabels(ax, bars, fmt="{:.1f}%", horizontal=True)
ax.set_xlim(0, share.max() * 100 * 1.2)
ax.set_xlabel("Share of all bookings")
ax.xaxis.set_major_formatter(PercentFormatter())
ax.grid(axis="y", visible=False)
finish(fig, ax, "eda15_region_concentration.png",
       "Two regions take a third of all bookings",
       f"Pokhara/Annapurna and Everest/Khumbu together hold {STATS['top2_region_share']*100:.0f}% of bookings. Ranking on popularity alone would widen that gap.",
       "Source: bookings.csv, 95,000 bookings")

# D3 - guide registry
fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.9),
                         gridspec_kw={"width_ratios": [1.25, 1, 1]})
ax = axes[0]
cert = guides["certification"].value_counts().sort_values()
bars = ax.barh(cert.index, cert.values, color=SEQ[3], height=0.6)
barlabels(ax, bars, horizontal=True, size=8.5)
ax.set_xlim(0, cert.max() * 1.22)
ax.set_title("Certification tier", fontsize=11.5, loc="left", pad=6)
ax.tick_params(axis="y", labelsize=8.5)
ax.grid(axis="y", visible=False)
ax = axes[1]
ax.hist(guides["average_rating"], bins=30, color=C["aqua"], alpha=0.9)
ax.axvline(guides["average_rating"].mean(), color=INK, ls="--", lw=1.4)
ax.annotate(f"mean {guides['average_rating'].mean():.2f}",
            (guides["average_rating"].mean(), ax.get_ylim()[1] * 0.92),
            xytext=(6, 0), textcoords="offset points", fontsize=9.5, color=INK)
ax.set_title("Average rating", fontsize=11.5, loc="left", pad=6)
ax.set_xlabel("Stars")
ax.grid(axis="x", visible=False)
ax = axes[2]
ver = guides["verification_status"].value_counts().sort_values()
bars = ax.barh(ver.index, ver.values, color=[C["red"], C["yellow"], GOOD][:len(ver)], height=0.55)
barlabels(ax, bars, horizontal=True, size=9)
ax.set_xlim(0, ver.max() * 1.25)
ax.set_title("Verification status", fontsize=11.5, loc="left", pad=6)
ax.grid(axis="y", visible=False)
STATS["guide_rating_mean"] = round(float(guides["average_rating"].mean()), 3)
STATS["guide_rating_sd"] = round(float(guides["average_rating"].std()), 3)
STATS["verification_status"] = {k: int(v) for k, v in
                                guides["verification_status"].value_counts().items()}
fig.tight_layout()
finish(fig, axes, "eda16_guide_registry.png",
       "Eight thousand guides, and ratings that hardly separate them",
       f"Ratings cluster near {STATS['guide_rating_mean']:.1f} with a standard deviation of {STATS['guide_rating_sd']:.2f}, so a star average carries little information about any one pairing.",
       "Source: verified_guides.csv")


# ===========================================================================
# PART E - model results
# ===========================================================================
print("\nPart E: model results")
tr = train_report


def g(path, default=None):
    node = tr
    for key in path.split("/"):
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


if tr:
    # E1 - recommender against baselines, both granularities
    strat = [
        ("Random", "random", SEQ[1]),
        ("Popularity (baseline)", "popularity", C["yellow"]),
        ("Hand-weighted heuristic", "content_heuristic_legacy", C["violet"]),
        ("Learned ranker", "learned_ranker", C["blue"]),
        ("Learned, deployed cap", "learned_ranker_max_3_per_trek", C["aqua"]),
    ]
    rows = [(lab, g(f"route_recommender/comparison/{k}/hit_rate_at_10"),
             g(f"route_recommender/comparison/{k}/concept_hit_rate_at_10"), col)
            for lab, k, col in strat]
    STATS["recommender"] = [{"strategy": r[0], "hr10": r[1], "concept_hr10": r[2]} for r in rows]
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2), sharey=True)
    for ax, idx, title in [(axes[0], 1, "Exact route hit-rate@10"),
                           (axes[1], 2, "Trek level hit-rate@10")]:
        vals = [r[idx] for r in rows]
        bars = ax.barh([r[0] for r in rows], vals, color=[r[3] for r in rows], height=0.6)
        barlabels(ax, bars, fmt="{:.4f}", horizontal=True, size=9.5)
        ax.set_xlim(0, max(vals) * 1.28)
        ax.set_title(title, fontsize=12, loc="left", pad=6)
        ax.grid(axis="y", visible=False)
        ax.invert_yaxis()
    fig.tight_layout()
    finish(fig, axes, "res01_recommender_baselines.png",
           "The learned ranker beats popularity, at both levels of granularity",
           "Every strategy is scored through the same harness on 2024 data only, for 2,898 travellers.",
           "Source: analytics-engine training report")

    # E2 - learned coefficients
    coefs = g("route_recommender/coefficients", {})
    cs = pd.Series(coefs).sort_values(key=np.abs)
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    colours = [C["red"] if v < 0 else C["blue"] for v in cs.values]
    bars = ax.barh(cs.index.str.replace("_", " "), cs.values, color=colours, height=0.6)
    for b, v in zip(bars, cs.values):
        ax.annotate(f"{v:+.4f}", (v, b.get_y() + b.get_height() / 2),
                    xytext=(6 if v >= 0 else -6, 0), textcoords="offset points",
                    va="center", ha="left" if v >= 0 else "right",
                    fontsize=9, color=INK2)
    ax.axvline(0, color=AXIS, lw=1.2)
    ax.set_xlim(cs.min() * 1.32, max(cs.max() * 2.4, 0.3))
    ax.set_xlabel("Standardised coefficient")
    ax.grid(axis="y", visible=False)
    finish(fig, ax, "res02_ranker_coefficients.png",
           "Given thirteen features, the model kept one",
           "The adventure gap dominates. Eight of the thirteen features are driven below 0.03, including every feature profiling had already shown to be flat.",
           "Source: analytics-engine training report")

    # E3 - diversity trade-off
    caps = [("No cap", "learned_ranker_variant_deduped"),
            ("Max 3 per trek", "learned_ranker_max_3_per_trek"),
            ("Max 2 per trek", "learned_ranker_max_2_per_trek"),
            ("Max 1 per trek", "learned_ranker_max_1_per_trek")]
    pop = g("route_recommender/comparison/popularity/hit_rate_at_10")
    vals = [g(f"route_recommender/comparison/{k}/hit_rate_at_10") for _, k in caps]
    lifts = [v / pop for v in vals]
    STATS["diversity_tradeoff"] = [{"cap": c[0], "hr10": v, "lift": round(l, 3)}
                                   for c, v, l in zip(caps, vals, lifts)]
    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    xs = [c[0] for c in caps]
    colours = [SEQ[2], C["aqua"], SEQ[2], SEQ[2]]
    bars = ax.bar(xs, vals, color=colours, width=0.55)
    for b, v, l in zip(bars, vals, lifts):
        ax.annotate(f"{v:.4f}\n{l:.2f}x baseline",
                    (b.get_x() + b.get_width() / 2, v), xytext=(0, 5),
                    textcoords="offset points", ha="center", fontsize=9.5, color=INK)
    ax.axhline(pop, color=C["yellow"], ls="--", lw=1.6)
    ax.annotate("popularity baseline", (3.35, pop), xytext=(0, 5),
                textcoords="offset points", ha="right", fontsize=9.5, color=INK2)
    ax.set_ylabel("Hit-rate@10")
    ax.set_ylim(0, max(vals) * 1.30)
    ax.grid(axis="x", visible=False)
    finish(fig, ax, "res03_diversity_tradeoff.png",
           "What the diversity cap costs, measured rather than assumed",
           "Collapsing to one row per trek returns the model to the baseline. A cap of three keeps most of the gain and still shows four or more different treks.",
           "Source: analytics-engine training report")

    # E4 - scam model comparison
    models = [("Majority baseline", "majority_baseline", SEQ[1]),
              ("Logistic regression", "logistic_regression", C["violet"]),
              ("Gradient boosting", "gradient_boosting", C["blue"])]
    metrics = ["accuracy", "f1", "roc_auc", "brier"]
    fig, axes = plt.subplots(1, 4, figsize=(10.4, 3.8))
    for ax, m in zip(axes, metrics):
        vals = [g(f"scam_classifier/comparison/{k}/{m}") for _, k, _ in models]
        bars = ax.bar([lab.split()[0] for lab, _, _ in models], vals,
                      color=[c for _, _, c in models], width=0.6)
        barlabels(ax, bars, fmt="{:.3f}", size=9)
        ax.set_ylim(0, max(max(vals) * 1.25, 0.05))
        ax.set_title({"accuracy": "Accuracy", "f1": "F1",
                      "roc_auc": "ROC-AUC", "brier": "Brier (lower is better)"}[m],
                     fontsize=11, loc="left", pad=6)
        ax.tick_params(axis="x", labelsize=9)
        ax.grid(axis="x", visible=False)
    fig.tight_layout()
    finish(fig, axes, "res04_scam_model_selection.png",
           "Accuracy was almost tied, so the model was chosen on calibration",
           "ROC-AUC separates the two learners by 0.0004. The Brier score separates them by a factor of eight, and the app shows a probability to a user.",
           "Source: analytics-engine training report, 2024 test year")

    # E5 - cold cell
    fig, ax = plt.subplots(figsize=(9.0, 3.6))
    labels = ["Logistic regression", "Gradient boosting"]
    seen = [g("scam_classifier/comparison/logistic_regression/f1"),
            g("scam_classifier/comparison/gradient_boosting/f1")]
    cold = [g("scam_classifier/cold_cell/logistic_regression/f1"),
            g("scam_classifier/cold_cell/gradient_boosting/f1")]
    y = np.arange(len(labels))
    h = 0.34
    b1 = ax.barh(y - h / 2, seen, height=h, color=C["blue"], label="Service and region seen in training")
    b2 = ax.barh(y + h / 2, cold, height=h, color=C["orange"], label="60 combinations never seen")
    barlabels(ax, b1, fmt="{:.3f}", horizontal=True, size=9.5)
    barlabels(ax, b2, fmt="{:.3f}", horizontal=True, size=9.5)
    ax.set_yticks(y, labels)
    ax.set_xlim(0, 1.16)
    ax.set_xlabel("F1")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=2)
    ax.grid(axis="y", visible=False)
    finish(fig, ax, "res05_scam_cold_cell.png",
           "The classifier still works on market segments it has never seen",
           f"Sixty complete service and region combinations were held out, giving {g('scam_classifier/cold_cell/n_test_rows'):,} unseen test rows.",
           "Source: analytics-engine training report")

    # E6 - guide ranker
    gr = [("Guide's own star average", "baseline_guide_average_rating", C["red"]),
          ("Predict the global mean", "baseline_global_mean", C["yellow"]),
          ("Gradient boosting", "gradient_boosting", C["violet"]),
          ("Ridge (deployed)", "ridge", C["blue"])]
    vals = [g(f"guide_ranker/comparison/{k}/rmse") for _, k, _ in gr]
    STATS["guide_ranker"] = dict(zip([x[0] for x in gr], vals))
    fig, ax = plt.subplots(figsize=(9.2, 3.8))
    bars = ax.barh([x[0] for x in gr], vals, color=[x[2] for x in gr], height=0.6)
    barlabels(ax, bars, fmt="{:.3f}", horizontal=True)
    ax.axvline(vals[1], color=INK, ls="--", lw=1.3)
    ax.annotate("no-model baseline", (vals[1], -0.62), xytext=(4, 0),
                textcoords="offset points", fontsize=9.5, color=INK2)
    ax.set_xlim(0, max(vals) * 1.18)
    ax.set_xlabel("RMSE on the 1 to 5 rating (lower is better)")
    ax.grid(axis="y", visible=False)
    finish(fig, ax, "res06_guide_matching.png",
           "Ranking guides by their star rating is worse than not modelling at all",
           f"On {g('guide_ranker/metrics/n_test'):,.0f} held-out ratings the star average scores worse than simply predicting the average for everyone.",
           "Source: analytics-engine training report")

    # E7 - forecast
    per_month = g("arrivals_forecaster/per_month", [])
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.3),
                            gridspec_kw={"width_ratios": [1.3, 1], "wspace": 0.55})
    ax = axes[0]
    if per_month:
        m = [p["month"] for p in per_month]
        ax.plot(m, [p["actual"] for p in per_month], color=INK, lw=2.4, label="Actual 2024")
        ax.plot(m, [p["predicted"] for p in per_month], color=C["orange"], lw=2.4,
                ls="--", label="Forecast")
        ax.set_xticks(m)
        ax.set_xlabel("Month of 2024")
        ax.set_ylabel("Arrivals")
        thousands(ax)
        ax.legend(loc="upper left")
        ax.grid(axis="x", visible=False)
    ax = axes[1]
    base = [("Last 12-month mean", "last_12_month_mean"),
            ("Seasonal naive", "seasonal_naive"),
            ("Seasonal naive x growth", "seasonal_naive_x_growth"),
            ("Log trend + seasonality", "log_trend_seasonal")]
    test = [g(f"arrivals_forecaster/comparison/{k}/mape") for _, k in base]
    val = [g(f"arrivals_forecaster/validation/{k}/mape") for _, k in base]
    STATS["forecast_mape_test"] = dict(zip([b[0] for b in base], test))
    STATS["forecast_mape_validation"] = dict(zip([b[0] for b in base], val))
    y = np.arange(len(base))
    h = 0.36
    b1 = ax.barh(y - h / 2, test, height=h, color=C["blue"], label="2024 test year")
    b2 = ax.barh(y + h / 2, [min(v, 160) for v in val], height=h, color=C["orange"],
                 label="2023 validation year")
    barlabels(ax, b1, fmt="{:.0f}%", horizontal=True, size=9)
    barlabels(ax, b2, fmt="{:.0f}%", horizontal=True, size=9)
    ax.set_yticks(y, [b[0] for b in base], fontsize=9)
    ax.set_xlim(0, 218)
    ax.set_xlabel("MAPE")
    ax.xaxis.set_major_formatter(PercentFormatter())
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=2, fontsize=9)
    ax.grid(axis="y", visible=False)
    finish(fig, axes, "res07_arrivals_forecast.png",
           "A good test year and a validation year that says the opposite",
           "The deployed model halves the seasonal naive error on 2024 and is the worst method on 2023. Three recovery years are not enough to choose between them.",
           "Source: analytics-engine training report")

    # E8 - segmentation
    sweep = g("tourist_segments/silhouette_sweep", {})
    prof = g("tourist_segments/behavioural_validation/profile", [])
    fig, axes = plt.subplots(1, 2, figsize=(9.8, 3.9))
    ax = axes[0]
    ks = [int(k.split("=")[1]) for k in sweep]
    vs = list(sweep.values())
    ax.plot(ks, vs, color=C["blue"], marker="o")
    ax.axhspan(0, 0.25, color=C["red"], alpha=0.07)
    ax.annotate("below 0.25 means no real separation", (ks[0], 0.235),
                fontsize=9.5, color=INK2)
    ax.set_ylim(0, 0.62)
    ax.set_xlabel("Number of clusters (k)")
    ax.set_ylabel("Silhouette score")
    ax.grid(axis="x", visible=False)
    ax = axes[1]
    if prof:
        labels = [f"Segment {p['segment']}" for p in prof]
        vals = [p["mean_difficulty"] for p in prof]
        bars = ax.bar(labels, vals, color=SEQ[3], width=0.6)
        barlabels(ax, bars, fmt="{:.3f}", size=9.5)
        lo, hi = min(vals), max(vals)
        ax.set_ylim(lo - (hi - lo) * 2.4, hi + (hi - lo) * 1.5)
        ax.set_ylabel("Mean booked difficulty")
        ax.tick_params(axis="x", labelsize=9)
        ax.grid(axis="x", visible=False)
        ax.annotate(f"spread {g('tourist_segments/behavioural_validation/difficulty_spread')} "
                    f"against pooled SD {g('tourist_segments/behavioural_validation/pooled_sd')}, "
                    f"d = {g('tourist_segments/behavioural_validation/effect_size_cohens_d')}",
                    (0.0, 1.03), xycoords="axes fraction", fontsize=9.5, color=INK2)
    fig.tight_layout()
    finish(fig, axes, "res08_segmentation.png",
           "K-means returns four groups, but the data has no natural groups",
           "The silhouette curve is flat and low at every k. The segments do differ in behaviour, by about a fifth of a standard deviation.",
           "Source: analytics-engine training report")

    # E9 - fairness audit
    groups = g("scam_classifier/fairness/groups", {})
    gd = pd.DataFrame(groups).T
    gd = gd.sort_values("actual_rate")
    fig, ax = plt.subplots(figsize=(9.4, 4.4))
    y = np.arange(len(gd))
    h = 0.36
    b1 = ax.barh(y - h / 2, gd["actual_rate"], height=h, color=SEQ[2],
                 label="Actual overcharge rate in the data")
    b2 = ax.barh(y + h / 2, gd["flag_rate"], height=h, color=C["blue"],
                 label="Rate the model flags")
    barlabels(ax, b1, fmt="{:.3f}", horizontal=True, size=9)
    barlabels(ax, b2, fmt="{:.3f}", horizontal=True, size=9)
    ax.set_yticks(y, [f"{i}  (n={int(n):,})" for i, n in zip(gd.index, gd["n"])], fontsize=9.5)
    ax.set_xlim(0, gd[["actual_rate", "flag_rate"]].to_numpy().max() * 1.32)
    ax.set_xlabel("Rate")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2)
    ax.grid(axis="y", visible=False)
    disp = g("scam_classifier/fairness/flag_rate_disparity")
    worst = float((gd["flag_rate"] - gd["actual_rate"]).abs().max())
    STATS["fairness_disparity"] = disp
    STATS["fairness_worst_calibration_gap"] = round(worst, 4)
    finish(fig, ax, "res09_fairness_audit.png",
           "The gap between groups is in the market, not in the classifier",
           f"Flag rate disparity is {disp}, above the project's 0.15 review gate. But the model tracks each group's real rate to within {worst:.3f}.",
           "Source: analytics-engine training report, continent used for audit only")

    # E10 - scorecard
    cards = [
        ("Anti-scam classifier", g("scam_classifier/metrics/f1"), "F1 0.980", "Strong", GOOD),
        ("Arrivals forecast", 1 - g("arrivals_forecaster/metrics/mape") / 100,
         "MAPE 17.2%", "Moderate", WARN),
        ("Route recommender", g("route_recommender/metrics/model_only_lift_over_popularity") / 2,
         "1.63x popularity", "Modest", WARN),
        ("Guide matching", g("guide_ranker/metrics/rmse_improvement_over_mean_pct") / 10,
         "4.8% over mean", "Marginal", "#ec835a"),
        ("Tourist segments", g("tourist_segments/metrics/silhouette"),
         "Silhouette 0.133", "Weak", CRIT),
    ]
    fig, ax = plt.subplots(figsize=(9.4, 3.8))
    labels = [c[0] for c in cards]
    vals = [c[1] for c in cards]
    bars = ax.barh(labels, vals, color=[c[4] for c in cards], height=0.6)
    for b, c in zip(bars, cards):
        ax.annotate(f"{c[2]}   ({c[3]})", (b.get_width(), b.get_y() + b.get_height() / 2),
                    xytext=(8, 0), textcoords="offset points", va="center",
                    fontsize=10, color=INK)
    ax.set_xlim(0, 1.55)
    ax.set_xticks([])
    ax.invert_yaxis()
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    finish(fig, ax, "res10_scorecard.png",
           "Five models, ordered by how much signal the data gave them",
           "The bar length is a rough strength index only. The label beside each bar carries the real result.",
           "Source: analytics-engine training report")

# ---------------------------------------------------------------------------
(OUT / "stats.json").write_text(json.dumps(STATS, indent=2, default=str), encoding="utf-8")
print(f"\nCharts written to {OUT}")
print(f"Stats written to {OUT / 'stats.json'}")
