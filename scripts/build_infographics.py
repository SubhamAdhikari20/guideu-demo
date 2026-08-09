"""Build the GuideU thesis cover page and figures.

Run from the repo root with the system Python (needs Pillow and Chrome):

    python scripts/build_infographics.py

Renders each figure to PNG via headless Chrome at 2x, then crops the trailing
white space so every figure is only as tall as its content. Output goes to
../Thesis_Infographics next to the repo.

Chart colours are the validated GuideU palette (teal / gold / violet / red),
which clears the lightness, chroma, colour-vision-deficiency separation,
normal-vision and contrast checks on both light and dark surfaces.
"""
from __future__ import annotations

import base64
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\Asus\BSc_Computing\Projects\final_year_project")
OUT = ROOT / "Thesis_Infographics"
BUILD = Path(__file__).parent / "html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

OUT.mkdir(exist_ok=True)
BUILD.mkdir(exist_ok=True)

LOGO = base64.b64encode((ROOT / "Important_Images" / "GuideU-logo.png").read_bytes()).decode()

# ---------------------------------------------------------------- design system
NAVY = "#0D1B34"
NAVY_2 = "#132443"
TEAL = "#138086"
TEAL_LIGHT = "#29B6C4"
GOLD = "#F5B400"
CRIMSON = "#E2231A"
GREEN = "#5FCF6B"

# Validated categorical chart palette (light surface).
S1, S2, S3, S4 = "#00949B", "#C77B00", "#4A3AA7", "#D03B3B"
INK, INK_2, MUTED = "#0B0B0B", "#52514E", "#898781"
GRID, AXIS, SURFACE = "#E1E0D9", "#C3C2B7", "#FFFFFF"

BASE_CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}}
.fig{{background:{SURFACE};color:{INK};padding:44px 52px;display:flex;flex-direction:column;
  height:100%;width:100%}}
.fig-head{{display:flex;align-items:center;gap:14px;padding-bottom:14px;
  border-bottom:3px solid {TEAL};margin-bottom:26px}}
.fig-head .bar{{width:8px;height:38px;background:{GOLD};border-radius:4px}}
.fig-head h1{{font-size:31px;font-weight:800;letter-spacing:-.4px;color:{NAVY}}}
.fig-head p{{font-size:14.5px;color:{INK_2};margin-top:3px}}
.foot{{margin-top:30px;padding-top:16px;border-top:1px solid {GRID};
  font-size:11.5px;color:{MUTED};display:flex;justify-content:space-between}}
.card{{background:#FBFBFA;border:1px solid {GRID};border-radius:14px;padding:20px 22px}}
.tag{{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.7px;
  text-transform:uppercase;padding:4px 10px;border-radius:20px}}
h2{{font-size:18px;font-weight:700;color:{NAVY}}}
.small{{font-size:13px;color:{INK_2};line-height:1.5}}
.tnum{{font-variant-numeric:tabular-nums}}
"""


def page(body: str, css: str = "", w: int = 1600, h: int = 1000) -> str:
    """Wrap a figure body in the shared .fig frame so it fills the whole canvas."""
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
html,body{{width:{w}px;height:{h}px;overflow:hidden}}
{css}</style></head><body><div class="fig">{body}</div></body></html>"""


def head(title: str, sub: str) -> str:
    return f'<div class="fig-head"><div class="bar"></div><div><h1>{title}</h1><p>{sub}</p></div></div>'


def foot(left: str, right: str = "GuideU — Subham Adhikari (14812262)") -> str:
    return f'<div class="foot"><span>{left}</span><span>{right}</span></div>'


FIGURES: dict[str, tuple[str, int, int]] = {}


def add(name: str, html: str, w: int = 1600, h: int = 1000) -> None:
    FIGURES[name] = (html, w, h if name.startswith("00_") else 1400)


# =============================================================== 00 cover page
add("00_cover_page", f"""<!doctype html><html><head><meta charset="utf-8"><style>
{BASE_CSS}
html,body{{width:1240px;height:1754px;overflow:hidden}}
body{{background:{NAVY};color:#fff;position:relative}}
.mtn{{position:absolute;left:0;right:0;top:392px;height:600px;overflow:hidden}}
.peak{{position:absolute;bottom:0;width:0;height:0;border-style:solid}}
.emblem{{position:absolute;top:452px;left:50%;transform:translateX(-50%);
  width:236px;height:236px;border-radius:50%;background:{NAVY_2};
  border:3px solid rgba(255,255,255,.16);display:grid;place-items:center;text-align:center}}
.emblem b{{display:block;font-size:52px;font-weight:800;color:{GOLD};letter-spacing:-1.5px}}
.emblem span{{display:block;font-size:14px;color:#C7D2E2;margin-top:2px;line-height:1.4}}
.emblem i{{display:block;font-size:11.5px;color:{TEAL_LIGHT};margin-top:9px;
  font-style:normal;letter-spacing:1.1px;font-weight:700}}
.rule{{position:absolute;top:992px;left:0;right:0;height:9px;background:{CRIMSON}}}
.logo{{display:block;margin:74px auto 0;width:330px}}
.tagline{{text-align:center;color:{GREEN};font-size:23px;font-weight:800;
  line-height:1.42;margin-top:22px;padding:0 92px}}
.badge{{position:absolute;top:1048px;left:50%;transform:translateX(-50%);
  background:{TEAL};color:#fff;font-size:19px;font-weight:700;
  padding:14px 34px;border-radius:32px;white-space:nowrap}}
.stats{{position:absolute;top:1150px;left:92px;right:92px;
  display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
.stat{{background:{NAVY_2};border:1px solid rgba(255,255,255,.13);
  border-radius:12px;padding:15px 8px;text-align:center}}
.stat b{{display:block;font-size:26px;color:{GOLD};font-weight:800}}
.stat span{{display:block;font-size:11.5px;color:#B9C4D6;margin-top:4px;line-height:1.35}}
.by{{position:absolute;top:1350px;left:92px;right:92px;
  display:flex;justify-content:space-between;padding-top:26px;
  border-top:1px solid rgba(255,255,255,.14)}}
.by h4{{font-size:12.5px;color:{GOLD};letter-spacing:1.3px;font-weight:800}}
.by b{{display:block;font-size:20px;margin-top:9px;font-weight:800}}
.by span{{display:block;font-size:14px;color:#B9C4D6;margin-top:3px}}
.date{{position:absolute;bottom:74px;left:0;right:0;text-align:center;
  font-size:16.5px;font-weight:700;letter-spacing:1.2px}}
.sub{{position:absolute;bottom:44px;left:0;right:0;text-align:center;
  font-size:12.5px;color:#8494AC}}
</style></head><body>
<img class="logo" src="data:image/png;base64,{LOGO}">
<div class="tagline">An AI-Driven, Data-Backed Platform for Trusted<br>Trip Planning and Verified Guide Booking in Nepal</div>
<div class="mtn">
  <div class="peak" style="left:-90px;border-width:0 250px 430px 250px;border-color:transparent transparent #16447A transparent"></div>
  <div class="peak" style="left:250px;border-width:0 330px 560px 330px;border-color:transparent transparent #103763 transparent"></div>
  <div class="peak" style="left:600px;border-width:0 400px 500px 400px;border-color:transparent transparent {TEAL_LIGHT} transparent"></div>
  <div class="peak" style="left:210px;border-width:0 120px 300px 120px;border-color:transparent transparent #9FB6CC transparent"></div>
</div>
<div class="emblem"><div><b>500K</b><span>rows of travel-planning<br>data, 10 linked tables</span>
  <i>5 ML MODELS TRAINED</i></div></div>
<div class="rule"></div>
<div class="badge">ST6006CEM &nbsp;·&nbsp; Final Thesis Report</div>
<div class="stats">
  <div class="stat"><b>500K</b><span>synthetic records<br>across 10 tables</span></div>
  <div class="stat"><b>5</b><span>machine-learning<br>models trained</span></div>
  <div class="stat"><b>99.1%</b><span>anti-scam<br>accuracy</span></div>
  <div class="stat"><b>5</b><span>agile sprints<br>delivered</span></div>
</div>
<div class="by">
  <div><h4>PREPARED BY</h4><b>SUBHAM ADHIKARI</b><span>Student ID: 14812262</span></div>
  <div style="text-align:right"><h4>SUBMITTED TO</h4><b>MANOJ SHRESTHA</b><span>Module Leader</span></div>
</div>
<div class="date">AUGUST 2026</div>
<div class="sub">BSc (Hons) Computing &nbsp;·&nbsp; Softwarica College / Coventry University</div>
</body></html>""", 1240, 1754)

# ==================================================== 01 theoretical framework
def theory_card(colour, num, theory, author, problem, feature):
    return f"""<div class="tcard">
      <div class="tnum-badge" style="background:{colour}">{num}</div>
      <h3>{theory}</h3><div class="auth">{author}</div>
      <div class="lbl">The problem it names</div><p>{problem}</p>
      <div class="arrow" style="color:{colour}">↓</div>
      <div class="resp" style="border-color:{colour}">
        <div class="lbl2" style="color:{colour}">GuideU's response</div>{feature}</div>
    </div>"""

add("fig01_theoretical_framework", page(
    head("Theoretical Framework",
         "Three ideas from economics and behavioural science — and the feature each one justifies")
    + f"""<div class="grid">
    {theory_card(S1, "1", "Information Asymmetry", "Akerlof (1970)",
      "The seller knows quality; the buyer cannot verify it. Buyers bargain on price alone, honest providers leave, and average quality falls — the market for lemons.",
      "<b>Verified guide registry</b> — a costly-to-fake signal.<br><b>Price benchmarking</b> — screening on evidence.")}
    {theory_card(S2, "2", "Bounded Rationality", "Simon (1955)",
      "People do not optimise. Under limited time and attention they satisfice — take the first option that is good enough. Scams exploit whoever is easiest to reach.",
      "<b>Personalised recommender</b> — performs the comparison a tired traveller cannot, and returns a shortlist they can actually judge.")}
    {theory_card(S3, "3", "Choice Architecture", "Thaler &amp; Sunstein (2008)",
      "There is no neutral way to present a choice. Whatever ranks first changes what people pick — so the ranker holds real power over money and safety.",
      "<b>Explainable ranking</b> — reasons computed from the model's own coefficients.<br><b>Fair-wage flag</b> — protects the supply side.")}
    </div>
    <div class="thesis-line">All three describe an <b>information gap</b>. Machine learning is the instrument this project uses to narrow it — not because the technology was available, but because each model answers a named theoretical problem.</div>
    """ + foot("Figure 1 — Theoretical framework"),
    css=f"""
    .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}}
    .tcard{{background:#FBFBFA;border:1px solid {GRID};border-radius:16px;padding:22px 22px 20px;position:relative}}
    .tnum-badge{{width:34px;height:34px;border-radius:50%;color:#fff;font-weight:800;
      font-size:17px;display:grid;place-items:center;margin-bottom:12px}}
    .tcard h3{{font-size:20px;color:{NAVY};font-weight:800;line-height:1.2}}
    .auth{{font-size:13px;color:{MUTED};margin:3px 0 14px;font-style:italic}}
    .lbl{{font-size:10.5px;font-weight:800;letter-spacing:.9px;color:{MUTED};
      text-transform:uppercase;margin-bottom:5px}}
    .tcard p{{font-size:13.5px;line-height:1.5;color:{INK_2}}}
    .arrow{{text-align:center;font-size:24px;margin:10px 0 6px;font-weight:800}}
    .resp{{border-left:4px solid;padding:11px 13px;background:#fff;border-radius:0 10px 10px 0}}
    .lbl2{{font-size:10.5px;font-weight:800;letter-spacing:.9px;text-transform:uppercase;margin-bottom:5px}}
    .resp{{font-size:13.5px;line-height:1.55;color:{INK}}}
    .thesis-line{{margin-top:24px;background:{NAVY};color:#fff;border-radius:14px;
      padding:18px 24px;font-size:15px;line-height:1.55}}
    .thesis-line b{{color:{GOLD}}}
    """, w=1600, h=1000))

# ============================================================= 02 ML pipeline
def stage(colour, num, title, lines):
    items = "".join(f"<li>{i}</li>" for i in lines)
    return f"""<div class="stage">
      <div class="sbadge" style="background:{colour}">{num}</div>
      <h3>{title}</h3><ul>{items}</ul></div>"""

add("fig02_ml_pipeline", page(
    head("Machine Learning Pipeline &amp; Evaluation",
         "From 500,000 synthetic rows to five served models — with every result checked against a baseline")
    + f"""<div class="flow">
      {stage(S1,"1","Data",["10 linked tables","500,000 rows","Fixed seed 20240519","All 10 tables used"])}
      <div class="chev">›</div>
      {stage(S1,"2","Profile",["Which signals exist?","Adventure→difficulty ✓","Budget→cost ✗","Density 0.001 → no CF"])}
      <div class="chev">›</div>
      {stage(S2,"3","Features",["Pair features","Leakage excluded","Protected attrs excluded","Season derived"])}
      <div class="chev">›</div>
      {stage(S3,"4","Train",["Train 2021–2023","Validate on 2023","Baseline first","Registry + model card"])}
      <div class="chev">›</div>
      {stage(S4,"5","Evaluate",["Test on 2024 only","vs 12 baselines","Fairness audit","Cold-cell test"])}
      <div class="chev">›</div>
      {stage(TEAL,"6","Serve",["FastAPI endpoints","Reasons returned","Graceful fallback","Mobile + admin"])}
    </div>
    <div class="split">
      <div class="card"><h2>Temporal split — never random</h2>
        <div class="tl">
          <div class="tl-seg" style="background:{S1}">2021</div>
          <div class="tl-seg" style="background:{S1}">2022</div>
          <div class="tl-seg" style="background:{S3}">2023 · validate</div>
          <div class="tl-seg" style="background:{S4}">2024 · TEST</div>
        </div>
        <p class="small" style="margin-top:12px">Models learn from 2021–2023 and are judged only on 2024. Model choice and decision thresholds are fixed on the 2023 validation year, so the reported operating point is never tuned on the split it reports. A random split would leak the future into training and inflate every number.</p>
      </div>
      <div class="card"><h2>The five models</h2>
        <table class="mt tnum">
          <tr><td><b>Route recommender</b></td><td>Logistic ranker</td><td class="v">1.63× popularity</td></tr>
          <tr><td><b>Anti-scam classifier</b></td><td>Gradient boosting</td><td class="v">F1 0.980</td></tr>
          <tr><td><b>Guide matcher</b></td><td>Ridge regression</td><td class="v">RMSE 0.655</td></tr>
          <tr><td><b>Arrivals forecaster</b></td><td>Log-trend + season</td><td class="v">MAPE 17.2%</td></tr>
          <tr><td><b>Tourist segments</b></td><td>K-means (k=4)</td><td class="v w">Silhouette 0.13</td></tr>
        </table>
        <p class="small" style="margin-top:10px">Every figure is reproducible with <code>python -m training.run_all</code>.</p>
      </div>
    </div>""" + foot("Figure 2 — ML pipeline and evaluation protocol"),
    css=f"""
    .flow{{display:flex;align-items:stretch;gap:6px;margin-bottom:24px}}
    .stage{{flex:1;background:#FBFBFA;border:1px solid {GRID};border-radius:13px;padding:15px 14px}}
    .sbadge{{width:26px;height:26px;border-radius:50%;color:#fff;font-weight:800;font-size:13px;
      display:grid;place-items:center;margin-bottom:9px}}
    .stage h3{{font-size:16.5px;color:{NAVY};font-weight:800;margin-bottom:8px}}
    .stage ul{{list-style:none}}
    .stage li{{font-size:12.3px;color:{INK_2};line-height:1.65;padding-left:11px;position:relative}}
    .stage li:before{{content:"";position:absolute;left:0;top:8px;width:4px;height:4px;
      border-radius:50%;background:{AXIS}}}
    .chev{{display:grid;place-items:center;font-size:27px;color:{AXIS};font-weight:300}}
    .split{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}
    .tl{{display:flex;gap:2px;margin-top:14px}}
    .tl-seg{{flex:1;color:#fff;font-size:12.5px;font-weight:700;text-align:center;
      padding:11px 4px;border-radius:4px}}
    .tl-seg:last-child{{flex:1.25}}
    .mt{{width:100%;border-collapse:collapse;margin-top:10px}}
    .mt td{{padding:7.5px 0;border-bottom:1px solid {GRID};font-size:13.5px;color:{INK_2}}}
    .mt td b{{color:{NAVY}}}
    .mt .v{{text-align:right;font-weight:800;color:{S1}}}
    .mt .w{{color:{MUTED}}}
    code{{background:#F0EFEC;padding:1px 5px;border-radius:4px;font-size:12px}}
    """, w=1600, h=1000))

# ======================================================== 03/04 aims + objectives
add("fig03_research_aims", page(
    head("Research Aim", "What this project set out to establish")
    + f"""<div class="aim-wrap">
      <div class="aim-main">
        <div class="tag" style="background:{GOLD};color:{NAVY}">Primary aim</div>
        <p class="big">To design, build and evaluate a mobile-first tourism platform that
        uses <b>machine learning on real travel-planning data</b> to reduce the information
        gap between tourists and informal-sector providers in Nepal — and to report
        honestly how far that actually works.</p>
      </div>
      <div class="aim-side">
        <div class="qa"><div class="qn" style="background:{S1}">RQ1</div>
          <p><b>Technical.</b> To what extent can ML services — a personalised recommender
          with price-benchmarking and scam-risk models — give tourists accurate, useful
          decision support when measured against sensible baselines on a temporal split?</p></div>
        <div class="qa"><div class="qn" style="background:{S3}">RQ2</div>
          <p><b>Ethical.</b> What risks arise when an AI platform mediates trust between
          tourists and informal providers, and how far can those risks be mitigated
          inside the design of the platform itself?</p></div>
      </div>
    </div>
    <div class="hyps">
      <div class="hyp"><div class="hh"><span class="hlabel" style="background:{S1}">H1</span>
        <span class="verdict ok">Supported</span></div>
        <p>Personalisation beats a popularity baseline by a meaningful margin.</p>
        <div class="ev">1.63× hit-rate@10 · popularity 0.0083 → model 0.0135</div></div>
      <div class="hyp"><div class="hh"><span class="hlabel" style="background:{S2}">H2</span>
        <span class="verdict ok">Supported</span></div>
        <p>The scam-risk model reaches at least 90% accuracy on held-out data.</p>
        <div class="ev">99.1% accuracy · F1 0.980 · holds at 0.958 on unseen cells</div></div>
      <div class="hyp"><div class="hh"><span class="hlabel" style="background:{S3}">H3</span>
        <span class="verdict part">Supported, weak test</span></div>
        <p>Fairness measures can be applied without large accuracy loss.</p>
        <div class="ev">Protected attributes excluded, 99.1% retained — but no
        accuracy-trading intervention was applied</div></div>
    </div>""" + foot("Figure 3 — Research aim, questions and hypotheses"),
    css=f"""
    .aim-wrap{{display:grid;grid-template-columns:1.05fr 1fr;gap:24px;margin-bottom:22px}}
    .aim-main{{background:{NAVY};border-radius:16px;padding:26px 28px;color:#fff}}
    .big{{font-size:21px;line-height:1.5;margin-top:16px}}
    .big b{{color:{GOLD}}}
    .aim-side{{display:flex;flex-direction:column;gap:14px}}
    .qa{{background:#FBFBFA;border:1px solid {GRID};border-radius:14px;padding:17px 19px;
      display:flex;gap:14px;flex:1}}
    .qn{{color:#fff;font-weight:800;font-size:13.5px;padding:6px 11px;border-radius:8px;
      height:fit-content}}
    .qa p{{font-size:14px;line-height:1.5;color:{INK_2}}}
    .qa p b{{color:{NAVY}}}
    .hyps{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}
    .hyp{{background:#FBFBFA;border:1px solid {GRID};border-radius:14px;padding:18px 20px}}
    .hh{{display:flex;align-items:center;justify-content:space-between;margin-bottom:11px}}
    .hlabel{{color:#fff;font-weight:800;font-size:13px;padding:5px 11px;border-radius:7px}}
    .verdict{{font-size:11.5px;font-weight:800;padding:5px 11px;border-radius:20px}}
    .ok{{background:#E3F3E8;color:#1B6B37}}
    .part{{background:#FBF0DC;color:#8A5B00}}
    .hyp p{{font-size:14px;line-height:1.45;color:{NAVY};font-weight:600}}
    .ev{{margin-top:10px;font-size:12.5px;color:{INK_2};background:#fff;
      border-left:3px solid {AXIS};padding:8px 11px;border-radius:0 7px 7px 0;line-height:1.45}}
    """, w=1600, h=1000))

def obj(n, colour, title, body, status):
    return f"""<div class="ocard">
      <div class="onum" style="color:{colour};border-color:{colour}">{n}</div>
      <div><h3>{title}</h3><p>{body}</p>
      <div class="ost">{status}</div></div></div>"""

add("fig04_research_objectives", page(
    head("Research Objectives", "Six objectives, and what was delivered against each")
    + f"""<div class="ogrid">
      {obj("01",S1,"Review the literature",
        "Recommender systems, review mining and deception detection, digital trust and information asymmetry, and the ethics of algorithmic recommendation.",
        "Delivered — 4 areas, 4 platform case studies")}
      {obj("02",S1,"Profile the dataset before modelling",
        "Establish which signals the 500,000-row Travel Planning data actually contains, rather than assuming its documentation is correct.",
        "Delivered — 3 signals confirmed, 5 found absent")}
      {obj("03",S2,"Build the ML services",
        "Recommendation, scam-risk scoring, guide matching, demand forecasting and cold-start segmentation, trained and registered with model cards.",
        "Delivered — 5 models, all 10 tables used")}
      {obj("04",S3,"Evaluate honestly against baselines",
        "Temporal splits, validation-year model selection, and every model reported next to a baseline scored through the same harness.",
        "Delivered — 12 baselines across 5 tasks")}
      {obj("05",S4,"Address the ethical risks in the design",
        "Exclude protected attributes, audit fairness per group, make ranking explainable, and protect providers from the platform's own price transparency.",
        "Delivered — audit + fair-wage flag in 2 services")}
      {obj("06",TEAL,"Integrate into a working product",
        "Serve every model through the API and surface it in the Flutter app and the Next.js admin dashboard, with graceful fallback when the ML service is down.",
        "Delivered — 5 sprints merged to main")}
    </div>""" + foot("Figure 4 — Research objectives and delivery status"),
    css=f"""
    .ogrid{{display:grid;grid-template-columns:1fr 1fr;gap:18px 24px}}
    .ocard{{display:flex;gap:16px;background:#FBFBFA;border:1px solid {GRID};
      border-radius:14px;padding:18px 20px}}
    .onum{{font-size:27px;font-weight:800;border-bottom:3px solid;height:fit-content;
      padding-bottom:2px;letter-spacing:-1px}}
    .ocard h3{{font-size:17.5px;color:{NAVY};font-weight:800;margin-bottom:6px}}
    .ocard p{{font-size:13.5px;line-height:1.5;color:{INK_2}}}
    .ost{{margin-top:10px;display:inline-block;font-size:11.5px;font-weight:700;
      color:#1B6B37;background:#E3F3E8;padding:5px 11px;border-radius:20px}}
    """, w=1600, h=1000))




# ============================================================ 05 agile sprints
SPRINTS = [
    ("Sprint 1", "Foundation", ["Monorepo + 5 services", "Docker, nginx, MLflow", "CI per service", "ADRs and docs"], S1),
    ("Sprint 2", "Core product", ["Auth, catalog, bookings", "Flutter app shell", "Destinations + guides", "Backend feature set"], S1),
    ("Sprint 3", "Transactions", ["Bookings + payments", "Reviews &amp; moderation", "Owner-scoped queries", "Payment confirm flow"], S2),
    ("Sprint 4", "Intelligence", ["Recommendations API", "Anti-scam price check", "Live chat + festivals", "Admin dashboard"], S3),
    ("Sprint 5", "Hardening", ["Workspace + currency", "SOS safety alerts", "Rate limiting, caching", "Deploy + e2e tests"], S4),
    ("Data phase", "The ML core", ["Profiled all 10 tables", "5 models trained", "12 baselines reported", "Fair-wage protection"], TEAL),
]
_cards = "".join(
    '<div class="sp"><div class="sp-top" style="background:%s"></div>'
    '<div class="sp-body"><div class="sp-n">%s</div><h3>%s</h3><ul>%s</ul></div></div>'
    % (c, n, t, "".join("<li>%s</li>" % i for i in items))
    for n, t, items, c in SPRINTS
)

add("fig05_agile_sprints", page(
    head("Agile Sprint History", "Five sprints delivered and merged to main, plus the data and ML phase that followed")
    + f"""<div class="track">{_cards}</div>
    <div class="lower">
      <div class="card"><h2>How version control mirrored the process</h2>
        <p class="small" style="margin-top:9px">One long-lived branch per sprint plus <code>main</code>. Each sprint branch was merged with a <code>--no-ff</code> release merge, so the history shows discrete increments rather than a flat line of commits. Commit messages are plain English throughout.</p>
        <div class="branches">
          <div class="br"><span class="dot" style="background:{S4}"></span>main</div>
          <div class="br"><span class="dot" style="background:{S1}"></span>sprint-1 … sprint-5</div>
          <div class="br"><span class="dot" style="background:{MUTED}"></span>backup/pre-sprint1</div>
        </div>
      </div>
      <div class="card"><h2>What MoSCoW actually decided</h2>
        <table class="mo">
          <tr><td><span class="pill must">MUST</span></td><td>Verified guides, discovery, bookings, recommendations</td><td class="y">Delivered</td></tr>
          <tr><td><span class="pill should">SHOULD</span></td><td>Chat, workspace, currency, safety SOS</td><td class="y">Delivered</td></tr>
          <tr><td><span class="pill could">COULD</span></td><td>Payment gateway crypto-verification, admin write actions</td><td class="n">Deferred</td></tr>
        </table>
        <p class="small" style="margin-top:11px">The deferred items are exactly the <b>could-haves</b>. That is prioritisation working as intended, not failure — and it is reported rather than quietly dropped.</p>
      </div>
    </div>""" + foot("Figure 5 — Agile sprint history and scope decisions"),
    css=f"""
    .track{{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-bottom:24px}}
    .sp{{background:#FBFBFA;border:1px solid {GRID};border-radius:13px;overflow:hidden}}
    .sp-top{{height:6px}}
    .sp-body{{padding:14px 15px}}
    .sp-n{{font-size:11px;font-weight:800;letter-spacing:.9px;color:{MUTED};text-transform:uppercase}}
    .sp h3{{font-size:17px;color:{NAVY};font-weight:800;margin:3px 0 9px}}
    .sp ul{{list-style:none}}
    .sp li{{font-size:12.2px;color:{INK_2};line-height:1.6;padding-left:11px;position:relative}}
    .sp li:before{{content:"";position:absolute;left:0;top:8px;width:4px;height:4px;border-radius:50%;background:{AXIS}}}
    .lower{{display:grid;grid-template-columns:1fr 1.15fr;gap:22px}}
    .branches{{margin-top:14px;display:flex;flex-direction:column;gap:9px}}
    .br{{display:flex;align-items:center;gap:9px;font-size:13.5px;color:{INK_2};font-family:ui-monospace,monospace}}
    .dot{{width:10px;height:10px;border-radius:50%}}
    .mo{{width:100%;border-collapse:collapse;margin-top:11px}}
    .mo td{{padding:8px 0;border-bottom:1px solid {GRID};font-size:13px;color:{INK_2};vertical-align:middle}}
    .pill{{font-size:10.5px;font-weight:800;padding:4px 9px;border-radius:5px;letter-spacing:.5px}}
    .must{{background:{NAVY};color:#fff}} .should{{background:{S1};color:#fff}} .could{{background:#E8E7E2;color:{INK_2}}}
    .mo .y{{text-align:right;color:#1B6B37;font-weight:700;white-space:nowrap}}
    .mo .n{{text-align:right;color:{MUTED};font-weight:700;white-space:nowrap}}
    code{{background:#F0EFEC;padding:1px 5px;border-radius:4px;font-size:12px}}
    """, w=1600, h=1000))

# ========================================================= 06 dataset overview
TABLES = [
    ("recommendation_interactions", 140000, "Ranking signal", S1),
    ("bookings", 95000, "Transaction history", S1),
    ("pricing_benchmarks", 85000, "Fair-price ground truth", S2),
    ("tourist_arrivals", 60000, "Forecasting series", S3),
    ("tourists", 40000, "Survey profiles", S1),
    ("scam_reports", 35000, "Labelled overcharges", S4),
    ("gamification_log", 31000, "Badges and points", S2),
    ("verified_guides", 8000, "NTB / IFMGA registry", S3),
    ("cultural_events", 4000, "Festival calendar", S2),
    ("trekking_routes", 2000, "Route catalog", S1),
]
_mx = max(r for _, r, _, _ in TABLES)
_rows = "".join(
    '<div class="trow"><div class="tname">%s</div>'
    '<div class="tbarwrap"><div class="tbar" style="width:%.1f%%;background:%s"></div></div>'
    '<div class="tval tnum">%s</div><div class="tuse">%s</div></div>'
    % (n, r / _mx * 100, c, f"{r:,}", u)
    for n, r, u, c in TABLES
)

add("fig06_dataset_overview", page(
    head("The Travel Planning Dataset", "500,000 synthetic records across ten linked tables — every one of them now feeds a model")
    + f"""<div class="dgrid">
      <div><div class="tbl">{_rows}</div>
        <p class="small" style="margin-top:16px">Synthetic by design. A pre-launch platform has no interaction history, and generating data avoids processing real guides' identities and livelihoods without their consent. The cost is external validity — stated here and revisited in the limitations.</p></div>
      <div class="side">
        <div class="kpi" style="border-color:{S1}"><b>500,000</b><span>rows across 10 linked tables</span></div>
        <div class="kpi" style="border-color:{S2}"><b>10 / 10</b><span>tables now used by a model<br><i>seven of ten before this work</i></span></div>
        <div class="kpi" style="border-color:{S3}"><b>2021–2024</b><span>train 2021–23 · validate 2023 · test 2024</span></div>
        <div class="card"><h2>Two structural limits</h2>
          <p class="small" style="margin-top:9px"><b>Sparsity.</b> Route-interaction density is 0.00106 and users average 1.15 positive events — too sparse for collaborative filtering. This was tested, not assumed: a user's own region history predicts their next region worse than guessing the most popular one.</p>
          <p class="small" style="margin-top:10px"><b>A cloned catalog.</b> 2,000 route rows carry 375 names covering only <b>26 real treks</b>. This caps route-level precision however good the model is.</p></div>
      </div>
    </div>""" + foot("Figure 6 — Dataset composition and structural limits"),
    css=f"""
    .dgrid{{display:grid;grid-template-columns:1.5fr 1fr;gap:30px}}
    .tbl{{display:flex;flex-direction:column;gap:9px}}
    .trow{{display:grid;grid-template-columns:225px 1fr 76px 168px;align-items:center;gap:13px}}
    .tname{{font-size:12.6px;color:{NAVY};font-weight:700;font-family:ui-monospace,monospace}}
    .tbarwrap{{height:19px;background:#F4F3F0;border-radius:4px;overflow:hidden}}
    .tbar{{height:100%;border-radius:0 4px 4px 0}}
    .tval{{font-size:13px;font-weight:800;color:{INK};text-align:right}}
    .tuse{{font-size:12.3px;color:{MUTED}}}
    .side{{display:flex;flex-direction:column;gap:13px}}
    .kpi{{background:#FBFBFA;border:1px solid {GRID};border-left:5px solid;border-radius:12px;padding:14px 18px}}
    .kpi b{{display:block;font-size:29px;font-weight:800;color:{NAVY};letter-spacing:-.5px}}
    .kpi span{{display:block;font-size:12.8px;color:{INK_2};margin-top:3px;line-height:1.45}}
    .kpi i{{color:{MUTED};font-size:12px}}
    """, w=1600, h=1000))


# ======================================================= 07 model vs baselines
# Small multiples: each task has its own metric and scale, so each gets its own
# panel rather than being forced onto one shared axis.
NEUTRAL = "#B3B1AA"

PANELS = [
    ("Route recommendation", "Hit-rate@10 &nbsp;·&nbsp; higher is better",
     [("Popularity baseline", 0.0083, "0.0083", NEUTRAL), ("Learned ranker", 0.0135, "0.0135", S1)],
     "1.63× the popularity baseline"),
    ("Anti-scam detection", "Accuracy &nbsp;·&nbsp; higher is better",
     [("Majority baseline", 0.786, "78.6%", NEUTRAL), ("Gradient boosting", 0.991, "99.1%", S1)],
     "F1 0.980 · Brier 0.006"),
    ("Guide matching", "RMSE &nbsp;·&nbsp; lower is better",
     [("Predict the mean", 0.688, "0.688", NEUTRAL), ("Ridge regression", 0.655, "0.655", S1)],
     "4.8% better than the mean"),
    ("Arrivals forecast", "MAPE &nbsp;·&nbsp; lower is better",
     [("Seasonal naive", 38.6, "38.6%", NEUTRAL), ("Log-trend model", 17.2, "17.2%", S1)],
     "Error roughly halved"),
]


def _panel(title, metric, bars, note):
    top = max(v for _, v, _, _ in bars) * 1.28
    cols = "".join(
        '<div class="bcol"><div class="blabel tnum">%s</div>'
        '<div class="bar" style="height:%.1f%%;background:%s"></div>'
        '<div class="bname">%s</div></div>' % (lab, v / top * 100, c, name)
        for name, v, lab, c in bars
    )
    return f"""<div class="panel"><h3>{title}</h3><div class="metric">{metric}</div>
      <div class="plot">{cols}</div><div class="note">{note}</div></div>"""


add("fig07_model_results", page(
    head("Model Results Against Baselines",
         "Every model reported next to a baseline scored through the same harness — test year 2024, never seen in training")
    + f"""<div class="legend">
      <span class="lg"><i style="background:{NEUTRAL}"></i>Baseline (no model)</span>
      <span class="lg"><i style="background:{S1}"></i>GuideU model</span>
    </div>
    <div class="panels">{"".join(_panel(*p) for p in PANELS)}</div>
    <div class="callouts">
      <div class="co"><h4>Why the recommender's absolute numbers are low</h4>
        <p>2,000 items, an average of 1.15 positive events per user, and a catalog that hides 26 real treks behind 375 names. A hit-rate@10 of 1.4% is close to what this data permits — so the defensible claim is the relative one, and it is stated that way throughout.</p></div>
      <div class="co"><h4>Why gradient boosting won the scam task</h4>
        <p>Not on accuracy — ROC-AUC was effectively tied with logistic regression (0.998 vs 0.999). It won on <b>calibration</b>: Brier 0.006 against 0.049. The app shows a probability to a user, so a well-calibrated score matters as much as a well-ranked one.</p></div>
      <div class="co"><h4>The comparison most projects skip</h4>
        <p>Ranking guides by their own star rating scores <b>RMSE 0.705 — worse than predicting the average for everyone</b>. A guide's aggregate rating poorly predicts how one particular traveller will rate them. That is the empirical case for matching over reputation sorting.</p></div>
    </div>""" + foot("Figure 7 — Model performance against baselines (test year 2024)"),
    css=f"""
    .legend{{display:flex;gap:26px;margin-bottom:16px}}
    .lg{{display:flex;align-items:center;gap:8px;font-size:13.5px;color:{INK_2};font-weight:600}}
    .lg i{{width:13px;height:13px;border-radius:3px;display:inline-block}}
    .panels{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:22px}}
    .panel{{background:#FBFBFA;border:1px solid {GRID};border-radius:14px;padding:17px 19px 15px}}
    .panel h3{{font-size:16.5px;color:{NAVY};font-weight:800}}
    .metric{{font-size:11.5px;color:{MUTED};margin:3px 0 6px;font-weight:600}}
    .plot{{height:186px;display:flex;align-items:flex-end;justify-content:center;gap:2px;
      border-bottom:2px solid {AXIS};padding:0 12px}}
    .bcol{{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;
      height:100%;max-width:76px;position:relative}}
    .bar{{width:100%;border-radius:4px 4px 0 0}}
    .blabel{{font-size:14px;font-weight:800;color:{INK};margin-bottom:5px}}
    .bname{{position:absolute;bottom:-32px;font-size:11px;color:{MUTED};text-align:center;
      line-height:1.3;width:100%}}
    .note{{margin-top:42px;font-size:12.3px;font-weight:700;color:{S1};text-align:center;
      background:#fff;border:1px solid {GRID};border-radius:8px;padding:7px 5px}}
    .callouts{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}}
    .co{{background:{NAVY};border-radius:13px;padding:16px 19px;color:#fff}}
    .co h4{{font-size:14px;color:{GOLD};font-weight:800;margin-bottom:7px}}
    .co p{{font-size:12.8px;line-height:1.55;color:#D5DDEA}}
    .co b{{color:#fff}}
    """, w=1600, h=1000))

# ========================================================= 08 fairness audit
FAIR = [
    ("East Asia", 0.154, 0.154, 1874), ("Europe", 0.306, 0.302, 1939),
    ("Latin America", 0.180, 0.180, 139), ("Middle East", 0.153, 0.147, 150),
    ("North America", 0.315, 0.320, 826), ("Oceania", 0.305, 0.308, 387),
    ("South Asia", 0.162, 0.162, 3227),
]
_TOP = 0.40
_groups = "".join(
    '<div class="fgroup"><div class="fbars">'
    '<div class="fbar" style="height:%.1f%%;background:%s"><span class="fv tnum">%.3f</span></div>'
    '<div class="fbar" style="height:%.1f%%;background:%s"><span class="fv tnum">%.3f</span></div>'
    '</div><div class="fname">%s</div><div class="fn tnum">n = %s</div></div>'
    % (m / _TOP * 100, S1, m, a / _TOP * 100, S2, a, name, f"{n:,}")
    for name, m, a, n in FAIR
)

add("fig08_fairness_audit", page(
    head("Fairness Audit — Anti-Scam Classifier",
         "The model never sees nationality. This chart asks whether it found a proxy for it anyway.")
    + f"""<div class="fwrap">
      <div class="chartbox">
        <div class="legend">
          <span class="lg"><i style="background:{S1}"></i>Model flag rate</span>
          <span class="lg"><i style="background:{S2}"></i>Actual overcharge rate</span>
        </div>
        <div class="fplot">{_groups}</div>
        <p class="axisnote">Proportion of quotes flagged, by tourist's continent · test year 2024</p>
      </div>
      <div class="fside">
        <div class="verdictbox">
          <div class="tag" style="background:#FBF0DC;color:#8A5B00">Gate: review</div>
          <b>0.1615</b><span>flag-rate disparity, against a 0.15 review gate — so the gate correctly routes this model to <b>human review, not silent deployment</b>.</span>
        </div>
        <div class="card"><h2>How to read it</h2>
          <p class="small" style="margin-top:9px">The two bars track each other in <b>every</b> group — the largest gap is 0.006. The model flags European and North American quotes about twice as often as East and South Asian ones because those tourists <b>genuinely are overcharged</b> about twice as often in this data.</p>
          <p class="small" style="margin-top:10px">A detector tuned to equalise flag rates would systematically <b>under-protect the tourists being targeted most</b>. The disparity lives in the market being modelled, not in the classifier.</p>
          <p class="small" style="margin-top:10px">This is a direct instance of <b>Chouldechova (2017)</b>: when base rates differ between groups, calibration and error-rate balance cannot both hold, and choosing between them is a normative decision rather than a technical one.</p>
        </div>
        <div class="mitig"><h4>Mitigations in code</h4>
          <ul><li>Protected attributes excluded from the feature set entirely</li>
              <li>Leaky features (ratio, benchmark) excluded too</li>
              <li>Audit runs on every training run, with a hard gate</li>
              <li>Every score returns benchmark, ratio and reasoning</li></ul></div>
      </div>
    </div>""" + foot("Figure 8 — Per-continent fairness audit of the anti-scam classifier"),
    css=f"""
    .fwrap{{display:grid;grid-template-columns:1.32fr 1fr;gap:28px;flex:1;min-height:0}}
    .chartbox{{background:#FBFBFA;border:1px solid {GRID};border-radius:15px;padding:20px 22px 16px;
      display:flex;flex-direction:column}}
    .legend{{display:flex;gap:26px;margin-bottom:18px}}
    .lg{{display:flex;align-items:center;gap:8px;font-size:13.5px;color:{INK_2};font-weight:600}}
    .lg i{{width:13px;height:13px;border-radius:3px;display:inline-block}}
    .fplot{{height:560px;display:flex;align-items:flex-end;gap:16px;
      border-bottom:2px solid {AXIS};padding-bottom:0}}
    .fgroup{{flex:1;display:flex;flex-direction:column;justify-content:flex-end;height:100%;position:relative}}
    .fbars{{display:flex;align-items:flex-end;justify-content:center;gap:2px;height:100%}}
    .fbar{{width:34px;border-radius:4px 4px 0 0;position:relative}}
    .fv{{position:absolute;top:-19px;left:0;right:0;text-align:center;font-size:11.5px;
      font-weight:800;color:{INK}}}
    .fname{{position:absolute;bottom:-24px;left:0;right:0;text-align:center;font-size:11.8px;
      color:{INK_2};font-weight:600}}
    .fn{{position:absolute;bottom:-39px;left:0;right:0;text-align:center;font-size:10.5px;color:{MUTED}}}
    .axisnote{{margin-top:52px;font-size:12px;color:{MUTED};text-align:center}}
    .fside{{display:flex;flex-direction:column;gap:14px}}
    .verdictbox{{background:{NAVY};border-radius:14px;padding:18px 21px;color:#fff}}
    .verdictbox b{{display:block;font-size:44px;font-weight:800;color:{GOLD};margin:9px 0 5px;letter-spacing:-1px}}
    .verdictbox span{{font-size:13px;line-height:1.55;color:#D5DDEA;display:block}}
    .verdictbox span b{{display:inline;font-size:13px;color:#fff;margin:0}}
    .mitig{{background:#FBFBFA;border:1px solid {GRID};border-radius:13px;padding:15px 19px}}
    .mitig h4{{font-size:14px;color:{NAVY};font-weight:800;margin-bottom:8px}}
    .mitig ul{{list-style:none}}
    .mitig li{{font-size:12.5px;color:{INK_2};line-height:1.6;padding-left:16px;position:relative}}
    .mitig li:before{{content:"✓";position:absolute;left:0;color:{S1};font-weight:800}}
    """, w=1600, h=1000))


# ================================================== 09 what the data supports
SIGNALS = [
    (True, "Adventure score → route difficulty", "1.81 → 3.25 across quintiles", "Monotonic and strong — the recommender's whole basis"),
    (True, "Overcharge ratio → scam flag", "Deterministic step at ratio ≈ 1.25", "Clean label; excluded as a feature to avoid leakage"),
    (True, "Certification → guide rating", "IFMGA 4.55 → City Guide 3.85", "Supports credential-based ranking"),
    (False, "Budget band → route cost", "2,112 / 2,109 / 2,107 / 2,094 USD", "Flat. The old heuristic spent 20% of its score here"),
    (False, "Culture score → region choice", "Region shares differ by under 2pp", "Flat across every quintile"),
    (False, "Nature score → altitude", "≈ 4,500 m in every quintile", "Flat"),
    (False, "Fitness level → difficulty", "2.535 / 2.528 / 2.524 / 2.522", "Flat"),
    (False, "Experience level → difficulty", "2.546 / 2.524 / 2.527 / 2.515", "Flat"),
]
_srows = "".join(
    '<div class="srow %s"><div class="sicon" style="background:%s">%s</div>'
    '<div class="sclaim">%s</div><div class="sval tnum">%s</div><div class="snote">%s</div></div>'
    % ("yes" if ok else "no", S1 if ok else NEUTRAL, "✓" if ok else "✕", claim, val, note)
    for ok, claim, val, note in SIGNALS
)

COEFS = [
    ("gap_adventure", -1.5924, 1.00), ("popularity", 0.1485, 0.093),
    ("pref_adventure_score", -0.0840, 0.053), ("duration_norm", 0.0536, 0.034),
    ("gap_cost", 0.0307, 0.019), ("other 8 features", 0.0300, 0.019),
]
_crows = "".join(
    '<div class="crow"><div class="cname">%s</div>'
    '<div class="cbarwrap"><div class="cbar" style="width:%.1f%%;background:%s"></div></div>'
    '<div class="cval tnum">%s</div></div>'
    % (n, w * 100, S1 if abs(v) > 0.1 else NEUTRAL, ("%+.4f" % v) if n != "other 8 features" else "all < 0.03")
    for n, v, w in COEFS
)

add("fig09_what_data_supports", page(
    head("What the Data Actually Supports",
         "Profiling came before modelling — and half the relationships the dataset documentation advertises are not in the data")
    + f"""<div class="wgrid">
      <div>
        <div class="colhead">Claimed signal &nbsp;→&nbsp; profiling result</div>
        <div class="stable">{_srows}</div>
        <p class="small" style="margin-top:15px">Five of eight advertised relationships are flat. A model can only find what the generator put there — which is why the profiling step exists, and why it is reported.</p>
      </div>
      <div>
        <div class="colhead">The learned recommender's own weights</div>
        <div class="ctable">{_crows}</div>
        <div class="punch">
          <h4>The finding this figure exists for</h4>
          <p>Given all thirteen features, the model put essentially <b>all</b> its weight on the single relationship the data supports and drove the rest to zero.</p>
          <p style="margin-top:9px">The previous hand-tuned version assigned <b>40% of its score</b> to budget fit and season fit — two dimensions carrying no information at all. Learning the weights found that out in one fit.</p>
        </div>
      </div>
    </div>""" + foot("Figure 9 — Data profiling results and the learned feature weights"),
    css=f"""
    .wgrid{{display:grid;grid-template-columns:1.32fr 1fr;gap:32px}}
    .colhead{{font-size:11.5px;font-weight:800;letter-spacing:.9px;text-transform:uppercase;
      color:{MUTED};padding-bottom:9px;border-bottom:2px solid {GRID};margin-bottom:12px}}
    .stable{{display:flex;flex-direction:column;gap:7px}}
    .srow{{display:grid;grid-template-columns:26px 1fr 210px 250px;align-items:center;gap:13px;
      padding:9px 12px;border-radius:9px}}
    .srow.yes{{background:#F1F8F4;border:1px solid #D6E9DE}}
    .srow.no{{background:#FAFAF8;border:1px solid {GRID}}}
    .sicon{{width:22px;height:22px;border-radius:50%;color:#fff;font-size:13px;font-weight:800;
      display:grid;place-items:center}}
    .sclaim{{font-size:13.5px;font-weight:700;color:{NAVY}}}
    .sval{{font-size:12.3px;color:{INK_2}}}
    .snote{{font-size:12px;color:{MUTED};line-height:1.35}}
    .ctable{{display:flex;flex-direction:column;gap:10px}}
    .crow{{display:grid;grid-template-columns:170px 1fr 82px;align-items:center;gap:12px}}
    .cname{{font-size:12.4px;font-family:ui-monospace,monospace;color:{NAVY};font-weight:600}}
    .cbarwrap{{height:18px;background:#F4F3F0;border-radius:4px;overflow:hidden}}
    .cbar{{height:100%;border-radius:0 4px 4px 0}}
    .cval{{font-size:12.3px;font-weight:800;color:{INK};text-align:right}}
    .punch{{margin-top:20px;background:{NAVY};border-radius:14px;padding:19px 22px;color:#fff}}
    .punch h4{{font-size:14.5px;color:{GOLD};font-weight:800;margin-bottom:9px}}
    .punch p{{font-size:13.5px;line-height:1.55;color:#D5DDEA}}
    .punch b{{color:#fff}}
    """, w=1600, h=1000))

# ====================================================== 10 system architecture
add("fig10_system_architecture", page(
    head("System Architecture", "Where each model lives, and what happens when the ML service does not answer")
    + f"""<div class="arch">
      <div class="layer">
        <div class="lname">Clients</div>
        <div class="boxes">
          <div class="box" style="border-color:{S1}"><b>Flutter mobile app</b>
            <span>Explore · Guides · Bookings · Price check · Trips · SOS</span>
            <i>Shows the ranker's reason on every recommendation card</i></div>
          <div class="box" style="border-color:{S1}"><b>Next.js admin dashboard</b>
            <span>Overview · ML models · Demand forecast · Festivals · Scam reports</span>
            <i>Server-side fetch so the ML key never reaches the browser</i></div>
        </div>
      </div>
      <div class="down">↓ &nbsp; REST + JWT &nbsp; ↓</div>
      <div class="layer">
        <div class="lname">Core engine</div>
        <div class="boxes">
          <div class="box wide" style="border-color:{S2}"><b>Django + DRF &nbsp;·&nbsp; PostgreSQL</b>
            <span>18 apps — auth, catalog, bookings, payments, trust, recommendations, workspace, currency, safety, chat, reviews, gamification</span>
            <i>Owns the catalog and every user-facing write. Falls back to a deterministic ordering whenever the ML service is unreachable, so the feed never breaks.</i></div>
          <div class="box" style="border-color:{S3}"><b>Node.js realtime</b>
            <span>Socket.IO chat, message persistence</span></div>
        </div>
      </div>
      <div class="down">↓ &nbsp; internal call, <code>X-API-Key</code> &nbsp; ↓</div>
      <div class="layer">
        <div class="lname">Analytics engine</div>
        <div class="mlbox">
          <div class="mlhead"><b>FastAPI &nbsp;·&nbsp; scikit-learn</b><span>Five registered models, each with a model card and a fallback path</span></div>
          <div class="models">
            <div class="m" style="border-top-color:{S1}"><b>route_recommender</b><span>Logistic ranker</span><i>/recommendations/routes</i></div>
            <div class="m" style="border-top-color:{S4}"><b>scam_classifier</b><span>Gradient boosting</span><i>/scam/score</i></div>
            <div class="m" style="border-top-color:{S2}"><b>guide_ranker</b><span>Ridge regression</span><i>/guides/rank</i></div>
            <div class="m" style="border-top-color:{S3}"><b>arrivals_forecaster</b><span>Log-trend + season</span><i>/forecast/arrivals</i></div>
            <div class="m" style="border-top-color:{TEAL}"><b>tourist_segments</b><span>K-means (k=4)</span><i>/segments/assign</i></div>
          </div>
        </div>
      </div>
      <div class="down">↑ &nbsp; trained from &nbsp; ↑</div>
      <div class="layer">
        <div class="lname">Data</div>
        <div class="boxes">
          <div class="box wide" style="border-color:{MUTED}"><b>Travel Planning dataset — 500,000 rows, 10 tables</b>
            <span>Held outside version control · fixed seed 20240519 · train 2021–23, validate 2023, test 2024</span></div>
          <div class="box" style="border-color:{MUTED}"><b>Model registry</b>
            <span>model_registry.json + optional MLflow</span></div>
        </div>
      </div>
    </div>""" + foot("Figure 10 — Service architecture and model placement"),
    css=f"""
    .arch{{display:flex;flex-direction:column;gap:5px}}
    .layer{{display:grid;grid-template-columns:112px 1fr;align-items:center;gap:17px}}
    .lname{{font-size:11.5px;font-weight:800;letter-spacing:1px;text-transform:uppercase;
      color:{MUTED};text-align:right}}
    .boxes{{display:flex;gap:14px}}
    .box{{flex:1;background:#FBFBFA;border:1px solid {GRID};border-left:5px solid;
      border-radius:11px;padding:12px 16px}}
    .box.wide{{flex:2.1}}
    .box b{{display:block;font-size:14.5px;color:{NAVY};font-weight:800}}
    .box span{{display:block;font-size:12.2px;color:{INK_2};margin-top:3px;line-height:1.45}}
    .box i{{display:block;font-size:11.5px;color:{MUTED};margin-top:6px;line-height:1.45}}
    .down{{text-align:center;font-size:11.5px;color:{AXIS};font-weight:700;letter-spacing:1px;
      padding:3px 0 3px 112px}}
    .mlbox{{background:{NAVY};border-radius:13px;padding:15px 18px}}
    .mlhead{{display:flex;align-items:baseline;gap:14px;margin-bottom:12px}}
    .mlhead b{{font-size:14.5px;color:#fff;font-weight:800}}
    .mlhead span{{font-size:12.2px;color:#9FB0C7}}
    .models{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
    .m{{background:{NAVY_2};border-top:4px solid;border-radius:9px;padding:11px 12px}}
    .m b{{display:block;font-size:12.6px;color:#fff;font-family:ui-monospace,monospace}}
    .m span{{display:block;font-size:11.3px;color:#9FB0C7;margin-top:3px}}
    .m i{{display:block;font-size:10.8px;color:{GOLD};margin-top:5px;font-family:ui-monospace,monospace;font-style:normal}}
    code{{background:#F0EFEC;padding:1px 5px;border-radius:4px;font-size:11.5px}}
    """, w=1600, h=1000))

# ==================================================================== render
def _trim_bottom(path: Path, pad_css_px: int = 44, scale: int = 2) -> tuple[int, int]:
    """Crop trailing white space so each figure is only as tall as its content.

    Figures carry different amounts of content, so a fixed canvas leaves an
    uneven white band under the shorter ones — which reads as a mistake once the
    image is placed in a Word document. Cropping to the last non-white row and
    restoring the page's own padding gives every figure the same visual margin.
    """
    from PIL import Image

    with Image.open(path) as im:
        rgb = im.convert("RGB")
        width, height = rgb.size
        pixels = rgb.load()
        last = height - 1
        step = max(width // 220, 1)
        while last > 0:
            row_is_blank = all(pixels[x, last] == (255, 255, 255) for x in range(0, width, step))
            if not row_is_blank:
                break
            last -= 1
        bottom = min(height, last + 1 + pad_css_px * scale)
        rgb.crop((0, 0, width, bottom)).save(path)
        return width, bottom


def render() -> None:
    for name, (html, w, h) in FIGURES.items():
        src = BUILD / f"{name}.html"
        src.write_text(html, encoding="utf-8")
        dest = OUT / f"{name}.png"
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
             "--force-device-scale-factor=2", f"--window-size={w},{h}",
             f"--screenshot={dest}", f"file:///{src}"],
            check=True, capture_output=True,
        )
        # The cover page is a full-bleed dark design — nothing to trim.
        if name.startswith("00_"):
            pw, ph = w * 2, h * 2
        else:
            pw, ph = _trim_bottom(dest)
        size = dest.stat().st_size // 1024
        print(f"  {name}.png  ({pw}x{ph}px, {size} KB)")


if __name__ == "__main__":
    print(f"Rendering {len(FIGURES)} figures to {OUT}")
    render()
    print("done")
