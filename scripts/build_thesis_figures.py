"""Cover page and infographics for the GuideU final-year thesis report.

Everything is rendered from HTML/CSS through headless Chrome at a 2.5x device
scale, so a 1500px design lands as a 3750px PNG. At the width these sit at in
the Word document that is roughly 590 DPI, which stays sharp when the report is
exported to PDF and zoomed.

Palette notes. The document chrome (headers, cards, rules) uses the report's own
Word theme greens so the images sit natively in the page. Data series use a
separate categorical palette, because the theme green does not separate from
amber under the common colour-vision deficiencies and encoding must not depend
on a colour a marker might not be able to tell apart.

Every number in these figures comes from
``services/analytics-engine/artifacts/training_report.json`` or from a direct
profile of the Travel Planning dataset. Nothing here is illustrative.

Usage:  python scripts/build_thesis_figures.py
"""
from __future__ import annotations

import base64
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\Asus\BSc_Computing\Projects\final_year_project")
OUT = ROOT / "Thesis_Figures"
BUILD = Path(__file__).resolve().parent / "_figure_html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SCALE = "2.5"

OUT.mkdir(exist_ok=True)
BUILD.mkdir(exist_ok=True)


def b64(p: Path) -> str:
    return base64.b64encode(p.read_bytes()).decode()


LOGO_GUIDEU = b64(ROOT / "GuideU-logo.png")
LOGO_COLLEGE = b64(ROOT / "softwarica_college_logo.png")

# --------------------------------------------------------------------------
# design system
# --------------------------------------------------------------------------
BASE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Segoe UI",system-ui,-apple-system,sans-serif;
  -webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}
.fig{background:#fff;color:#17201A;display:flex;flex-direction:column;
  width:100%;padding:0 0 30px 0;position:relative}

/* header ---------------------------------------------------------------- */
.hdr{padding:30px 46px 20px 46px;position:relative}
.hdr:before{content:"";position:absolute;left:0;top:0;bottom:0;width:11px;
  background:linear-gradient(180deg,#90C226 0%,#6B911C 100%)}
.kick{font-size:16.1px;letter-spacing:2.6px;text-transform:uppercase;
  color:#6B911C;font-weight:700}
.hdr h1{font-size:40.9px;font-weight:700;letter-spacing:-.4px;color:#2C3B22;
  margin-top:7px;line-height:1.14}
.hdr p{font-size:19.2px;color:#5A655C;margin-top:9px;max-width:1220px;
  line-height:1.45}
.body{padding:4px 46px 0 46px;display:flex;flex-direction:column}

/* footer ---------------------------------------------------------------- */
.foot{margin:22px 46px 0 46px;padding-top:12px;border-top:1px solid #E2E8DA;
  display:flex;justify-content:space-between;font-size:14.9px;color:#98A093}
.foot b{color:#6B911C;font-weight:600}

/* cards ----------------------------------------------------------------- */
.card{background:#FBFDF7;border:1px solid #E2E8DA;border-radius:14px;
  padding:18px 20px;position:relative}
.card.solid{background:#fff;box-shadow:0 1px 3px rgba(30,48,20,.06)}
.card h3{font-size:21.7px;color:#3E5514;font-weight:700;margin-bottom:8px;
  line-height:1.25}
.card p,.small{font-size:16.7px;color:#4E594F;line-height:1.55}
.card p+p{margin-top:8px}
.tint{background:#F1F8E2;border-color:#DCE9C4}
.dark{background:#3E5514;border-color:#3E5514;color:#fff}
.dark h3{color:#C8E58A}
.dark p{color:#DFE9CE}

.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.grid5{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}
.row{display:flex;gap:16px}
.col{display:flex;flex-direction:column;gap:14px}
.col.eq>.card:first-child{flex:1}
.fill{flex:1}

/* numbered / label chrome ----------------------------------------------- */
.num{width:30px;height:30px;border-radius:50%;background:#90C226;color:#fff;
  font-size:18.6px;font-weight:700;display:flex;align-items:center;
  justify-content:center;flex:none}
.pill{display:inline-block;font-size:14.3px;font-weight:700;letter-spacing:.6px;
  text-transform:uppercase;padding:4px 11px;border-radius:20px;
  background:#E9F6D0;color:#4A6316}
.pill.ok{background:#DFF3E2;color:#1F6B34}
.pill.no{background:#FBE3E1;color:#9A2F26}
.pill.mid{background:#FDF0D9;color:#8A5A00}
.pill.ink{background:#E7ECE9;color:#465049}

/* stats ----------------------------------------------------------------- */
.stat{background:#F1F8E2;border-radius:13px;padding:16px 14px;text-align:center}
.stat b{display:block;font-size:42.2px;font-weight:700;color:#3E5514;line-height:1;
  font-variant-numeric:tabular-nums}
.stat span{display:block;font-size:15.5px;color:#57624F;margin-top:7px;
  line-height:1.35}
.stat.t{background:#E4F3F4}.stat.t b{color:#00707A}
.stat.a{background:#FCF0DC}.stat.a b{color:#A66400}
.stat.v{background:#EAE7F7}.stat.v b{color:#4A3AA7}
.stat.r{background:#FBE7E5}.stat.r b{color:#B03A2B}

/* bars ------------------------------------------------------------------ */
.bars{display:flex;flex-direction:column;gap:9px}
.brow{display:grid;grid-template-columns:190px 1fr 92px;align-items:center;
  gap:12px;font-size:16.1px}
.blab{color:#3E5514;font-weight:600;text-align:right}
.btrk{height:22px;background:#F0F2EC;border-radius:6px;overflow:hidden}
.bfil{height:100%;border-radius:6px}
.bval{color:#46514A;font-weight:700;font-variant-numeric:tabular-nums}
.bsub{font-size:14.3px;color:#98A093;font-weight:400}

/* column charts --------------------------------------------------------- */
.cols{display:flex;align-items:flex-end;gap:10px;height:330px}
.cwrap{flex:1;display:flex;flex-direction:column;align-items:center;
  justify-content:flex-end;height:100%}
.cv{font-size:16.1px;font-weight:700;color:#2C3B22;margin-bottom:5px;
  font-variant-numeric:tabular-nums}
.cbar{width:100%;border-radius:6px 6px 0 0}
.cl{font-size:14.3px;color:#6D766C;margin-top:7px;text-align:center;line-height:1.3}
.axis{border-top:1.5px solid #D6DCCE;margin-top:0}

/* tables ---------------------------------------------------------------- */
table.t{width:100%;border-collapse:collapse;font-size:16.1px}
table.t th{background:#3E5514;color:#fff;font-weight:600;font-size:14.9px;
  text-align:left;padding:9px 12px;letter-spacing:.3px}
table.t th:first-child{border-radius:8px 0 0 0}
table.t th:last-child{border-radius:0 8px 0 0}
table.t td{padding:9px 12px;border-bottom:1px solid #E7ECDF;color:#46514A;
  vertical-align:top}
table.t tr:nth-child(even) td{background:#FAFCF5}
table.t td.n{font-variant-numeric:tabular-nums;font-weight:600;color:#2C3B22}
table.t tr.hi td{background:#EDF7DA;font-weight:600;color:#2C3B22}

/* flow arrows ------------------------------------------------------------ */
.arrow{display:flex;align-items:center;justify-content:center;color:#A9BE7C;
  font-size:32.2px;font-weight:300;flex:none;width:34px}
.vsep{height:1px;background:#E2E8DA;margin:14px 0}
b.hl{color:#3E5514}
em{color:#00707A;font-style:normal;font-weight:600}
code{background:#EEF3E4;padding:1px 5px;border-radius:4px;font-size:14.9px;
  font-family:Consolas,monospace;color:#3E5514}
"""

FIGS: dict[str, tuple[str, int, int]] = {}


def page(body: str, css: str = "", w: int = 1500, h: int = 1500) -> str:
    return (
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        + BASE_CSS
        + f"html,body{{width:{w}px;height:{h}px;overflow:hidden}}"
        + css
        + f'</style></head><body><div class="fig">{body}</div></body></html>'
    )


def head(kick: str, title: str, sub: str = "") -> str:
    s = f"<p>{sub}</p>" if sub else ""
    return f'<div class="hdr"><div class="kick">{kick}</div><h1>{title}</h1>{s}</div>'


def foot(left: str) -> str:
    return (
        f'<div class="foot"><span>{left}</span>'
        '<span><b>GuideU</b> &nbsp;·&nbsp; Subham Adhikari &nbsp;·&nbsp; 14812262</span></div>'
    )


def add(name: str, body: str, css: str = "", w: int = 1500, h: int = 1500) -> None:
    FIGS[name] = (page(body, css, w, h), w, h)


def bar(label: str, pct: float, value: str, colour: str, sub: str = "") -> str:
    s = f' <span class="bsub">{sub}</span>' if sub else ""
    return (
        f'<div class="brow"><div class="blab">{label}</div>'
        f'<div class="btrk"><div class="bfil" style="width:{pct}%;background:{colour}"></div></div>'
        f'<div class="bval">{value}{s}</div></div>'
    )


def col(value: str, pct: float, label: str, colour: str) -> str:
    return (
        f'<div class="cwrap"><div class="cv">{value}</div>'
        f'<div class="cbar" style="height:{pct}%;background:{colour}"></div>'
        f'<div class="cl">{label}</div></div>'
    )


TEAL, AMBER, INDIGO, CRIMSON, SLATE = "#00838F", "#C77B00", "#4A3AA7", "#C0392B", "#68766B"
GREY = "#C3CABB"


# ==========================================================================
# COVER PAGE
# ==========================================================================
COVER_CSS = """
html,body{width:1240px;height:1754px;overflow:hidden}
body{background:#06120D}
.pg{position:absolute;inset:0;overflow:hidden;
  background:linear-gradient(178deg,#0C2C20 0%,#123D2A 38%,#0E3123 62%,#0A2419 100%)}
.glow{position:absolute;left:50%;top:-340px;width:1300px;height:1300px;
  transform:translateX(-50%);border-radius:50%;
  background:radial-gradient(circle,rgba(144,194,38,.26) 0%,rgba(0,131,143,.10) 45%,
    rgba(144,194,38,0) 68%)}
.mesh{position:absolute;inset:0;opacity:.11;
  background-image:linear-gradient(#90C226 1px,transparent 1px),
    linear-gradient(90deg,#90C226 1px,transparent 1px);
  background-size:58px 58px;
  -webkit-mask-image:radial-gradient(78% 46% at 50% 30%,#000 0%,transparent 76%)}
.edge{position:absolute;left:0;right:0;height:9px;z-index:20;
  background:linear-gradient(90deg,#90C226,#E8C547 48%,#00A2AE)}

.plate{position:absolute;top:56px;left:50%;transform:translateX(-50%);
  background:#fff;border-radius:14px;padding:19px 40px;
  box-shadow:0 16px 44px rgba(0,0,0,.40)}
.plate img{display:block;width:404px}
.mod{position:absolute;top:236px;left:50%;transform:translateX(-50%);
  border:1.5px solid rgba(169,210,94,.60);border-radius:30px;
  padding:9px 32px;font-size:14px;letter-spacing:4.2px;color:#BFE07C;
  font-weight:700;font-family:"Segoe UI",sans-serif;white-space:nowrap;
  background:rgba(144,194,38,.07)}
.mark{position:absolute;top:306px;left:50%;transform:translateX(-50%);width:272px}

.ttl{position:absolute;top:450px;left:74px;right:74px;text-align:center;
  font-family:Cambria,Georgia,serif;font-size:42px;line-height:1.25;
  font-weight:700;color:#fff;letter-spacing:-.3px}
.ttl em{color:#B4DC66;font-style:normal}
.uline{position:absolute;top:632px;left:50%;transform:translateX(-50%);
  width:126px;height:4px;border-radius:3px;
  background:linear-gradient(90deg,#90C226,#E8C547)}
.tag{position:absolute;top:664px;left:168px;right:168px;text-align:center;
  font-family:Cambria,Georgia,serif;font-style:italic;font-size:19px;
  line-height:1.6;color:#9DB7A6}

.chips{position:absolute;top:790px;left:0;right:0;display:flex;
  justify-content:center;gap:13px;font-family:"Segoe UI",sans-serif}
.chip{border:1px solid rgba(255,255,255,.16);border-radius:9px;padding:11px 20px;
  background:rgba(255,255,255,.05);text-align:center;min-width:150px}
.chip b{display:block;font-size:24px;font-weight:700;color:#B4DC66;line-height:1}
.chip span{display:block;font-size:11.5px;color:#8FA598;margin-top:5px;
  letter-spacing:.5px}

/* ground band the range stands on */
.ground{position:absolute;left:0;right:0;bottom:0;height:404px;
  background:linear-gradient(180deg,#08201A 0%,#061512 55%,#040E0B 100%)}
.haze{position:absolute;left:0;right:0;bottom:404px;height:260px;z-index:0;
  background:radial-gradient(60% 100% at 50% 100%,rgba(144,194,38,.16) 0%,
    rgba(144,194,38,0) 70%)}
.ridge{position:absolute;left:0;right:0;bottom:404px;height:2px;z-index:14;
  background:linear-gradient(90deg,rgba(144,194,38,0),#90C226 25%,#E8C547 52%,
    #00A2AE 76%,rgba(0,162,174,0))}
.range{position:absolute;left:0;right:0;bottom:404px;height:396px}
.mt{position:absolute;bottom:0}
.snow{position:absolute}
.trail{position:absolute;bottom:456px;left:0;right:0;height:410px;z-index:12}
.node{position:absolute;width:11px;height:11px;border-radius:50%;
  background:#E8C547;box-shadow:0 0 0 4px rgba(232,197,71,.22)}

.dtl{position:absolute;bottom:128px;left:88px;right:88px;
  display:grid;grid-template-columns:1fr 1fr;gap:38px 40px;
  font-family:"Segoe UI",sans-serif;z-index:15}
.d h4{font-size:11px;letter-spacing:2.4px;color:#8FB24E;font-weight:700;
  text-transform:uppercase}
.d p{font-size:20.5px;color:#fff;font-weight:600;margin-top:7px}
.d.r{text-align:right}
.dline{position:absolute;bottom:288px;left:88px;right:88px;height:1px;
  background:rgba(255,255,255,.13);z-index:15}
.sig{position:absolute;bottom:52px;left:0;right:0;text-align:center;
  font-family:"Segoe UI",sans-serif;font-size:12.5px;letter-spacing:2px;
  color:#6E8478;z-index:15}
.sig b{color:#A9C67E;font-weight:600}
"""


def _peak(left: int, w: int, h: int, colour: str, z: int = 1) -> str:
    """One mountain, drawn with a clip-path so the edges stay crisp at any scale."""
    return (
        f'<div class="mt" style="left:{left}px;width:{w}px;height:{h}px;z-index:{z};'
        f'background:{colour};clip-path:polygon(50% 0,100% 100%,0 100%)"></div>'
    )


def _cap(left: int, w: int, h: int, frac: float, z: int = 9) -> str:
    """Snow cap covering the top ``frac`` of a peak."""
    ch = h * frac
    cw = w * frac
    cx = left + w / 2 - cw / 2
    return (
        f'<div class="snow" style="left:{cx:.0f}px;bottom:{h - ch:.0f}px;'
        f'width:{cw:.0f}px;height:{ch:.0f}px;z-index:{z};background:#EDF3E6;'
        f'clip-path:polygon(50% 0,100% 100%,80% 88%,62% 100%,44% 86%,24% 98%,0 100%)"></div>'
    )


COVER = f"""<!doctype html><html><head><meta charset="utf-8"><style>{BASE_CSS}{COVER_CSS}
</style></head><body><div class="pg">
<div class="glow"></div><div class="mesh"></div>
<div class="edge" style="top:0"></div>

<div class="plate"><img src="data:image/png;base64,{LOGO_COLLEGE}"></div>
<div class="mod">ST6001CEM &nbsp;&middot;&nbsp; INDIVIDUAL PROJECT</div>
<img class="mark" src="data:image/png;base64,{LOGO_GUIDEU}">

<div class="ttl">An AI-Driven and Data-Backed Platform for<br>
Trusted Trip Planning and<br><em>Verified Guide Booking</em> in Nepal</div>
<div class="uline"></div>
<div class="tag">Machine learning on 500,000 records of travel-planning data,
built to close the information gap between tourists and Nepal's
informal-sector providers</div>

<div class="chips">
  <div class="chip"><b>500,000</b><span>ROWS OF DATA</span></div>
  <div class="chip"><b>5</b><span>ML MODELS</span></div>
  <div class="chip"><b>5</b><span>AGILE SPRINTS</span></div>
  <div class="chip"><b>99.1%</b><span>ANTI-SCAM ACCURACY</span></div>
</div>

<div class="ground"></div>
<div class="haze"></div>
<div class="range">
  {_peak(-210, 540, 240, "#0A2418", 1)}
  {_peak(270, 470, 216, "#0A2418", 1)}
  {_peak(910, 520, 258, "#0A2418", 1)}
  {_peak(-60, 500, 302, "#123C2A", 2)}
  {_peak(750, 540, 326, "#123C2A", 2)}
  {_cap(750, 540, 326, 0.20, 8)}
  {_peak(240, 640, 392, "#1B5A3E", 3)}
  {_cap(240, 640, 392, 0.22, 9)}
  {_peak(-10, 340, 208, "#25714A", 4)}
  {_cap(-10, 340, 208, 0.20, 10)}
  {_peak(650, 380, 228, "#25714A", 4)}
  {_cap(650, 380, 228, 0.19, 10)}
</div>
<div class="ridge"></div>

<div class="dline"></div>
<div class="dtl">
  <div class="d"><h4>Submitted by</h4><p>Subham Adhikari</p></div>
  <div class="d r"><h4>Module Leader</h4><p>Manoj Shrestha</p></div>
  <div class="d"><h4>Coventry Student ID</h4><p>14812262</p></div>
  <div class="d r"><h4>Due Date</h4><p>August 20, 2026</p></div>
</div>
<div class="sig">SOFTWARICA COLLEGE OF IT &amp; E-COMMERCE &nbsp;&middot;&nbsp;
IN COLLABORATION WITH <b>COVENTRY UNIVERSITY</b></div>
<div class="edge" style="bottom:0"></div>
</div></body></html>"""

FIGS["00_cover_page"] = (COVER, 1240, 1754)



# ==========================================================================
# CHAPTER 1 — INTRODUCTION
# ==========================================================================
add("fig01_tourism_context", head(
    "Chapter 1 · Background",
    "Nepal's Tourism Has Recovered, the Way People Plan It Has Not",
    "Arrivals are back to roughly pre-pandemic levels, but nothing was added in "
    "those years to help a visitor check a guide, a permit or a price.")
    + '<div class="body">'
    + '<div class="grid4" style="margin-bottom:18px">'
    + '<div class="stat"><b>1,147,567</b><span>arrivals in 2024<br>Nepal Tourism Board</span></div>'
    + '<div class="stat t"><b>+13.1%</b><span>growth on the<br>1,014,882 of 2023</span></div>'
    + '<div class="stat a"><b>6.6%</b><span>of national GDP from<br>travel and tourism</span></div>'
    + '<div class="stat v"><b>1.19m</b><span>jobs supported<br>across the sector</span></div>'
    + '</div>'
    + '<div class="row">'
    + '<div class="card fill">'
    + '<h3>Arrivals, 2019 to 2024</h3>'
    + '<div class="cols" style="margin-top:6px">'
    + col("1,197,191", 96, "2019<br>pre-pandemic peak", SLATE)
    + col("230,085", 19, "2020<br>borders shut", GREY)
    + col("150,962", 13, "2021<br>lowest point", GREY)
    + col("614,148", 50, "2022<br>reopening", "#8FB24E")
    + col("1,014,882", 82, "2023<br>recovery", "#6B911C")
    + col("1,147,567", 92, "2024<br>96% of the peak", "#90C226")
    + '</div><div class="axis"></div>'
    + '<p class="small" style="margin-top:12px">About 3,000 people arriving every day '
      'across the year. The industry got its volume back, and the planning experience '
      'stayed exactly where it was in 2019.</p>'
    + '</div>'
    + '<div class="col" style="width:430px">'
    + '<div class="card tint"><h3>What changed on the rules side</h3>'
      '<p>From <b class="hl">1 April 2023</b> every foreign trekker on the main routes '
      'must hire a licensed guide through a registered agency. Solo trekking on Everest '
      'Base Camp and the Annapurna circuits ended.</p></div>'
    + '<div class="card dark"><h3>What did not change</h3>'
      '<p>The rule made hiring a guide compulsory. It did not give anybody a way of '
      'judging <b style="color:#fff">which</b> guide to hire, or what that guide should '
      'cost. Regulation widened the information problem instead of closing it.</p></div>'
    + '</div></div></div>'
    + foot("Nepal tourism in context"))


add("fig02_trust_gap", head(
    "Chapter 1 · Problem context",
    "Five Things a Visitor Cannot Check, and Who Pays for It",
    "The problem is not a shortage of information. It is that none of the "
    "information available can be verified before money changes hands.")
    + '<div class="body">'
    + '<div class="grid5" style="margin-bottom:16px">'
    + ''.join(
        f'<div class="card solid" style="text-align:center;padding:16px 12px">'
        f'<div class="num" style="margin:0 auto 10px;background:{c}">{i}</div>'
        f'<h3 style="font-size:18.6px">{t}</h3>'
        f'<p style="font-size:15.5px">{d}</p></div>'
        for i, (t, d, c) in enumerate([
            ("Is the licence real?",
             "A card and a jacket look the same as ten years in the Khumbu.", "#90C226"),
            ("Is this price fair?",
             "No published benchmark, so the first quote sets the whole negotiation.", TEAL),
            ("Is the review honest?",
             "Ratings cluster at the top and carry very little information.", AMBER),
            ("Is the permit needed?",
             "Requirements sit across several sites and are not always current.", INDIGO),
            ("Is the route open?",
             "Seasonal closures change and word of mouth goes stale.", CRIMSON),
        ], start=1))
    + '</div>'
    + '<div class="row" style="gap:18px">'
    + '<div class="card fill"><h3>The cost falls on the tourist</h3>'
      '<p>Overcharging, taxi and permit scams, and unlicensed street guides taking '
      'visitors to shops for a commission. A visitor who cannot tell quality apart '
      'bargains on price alone, because price is the only thing they can actually see.</p>'
      '<p>Planning ends up spread over government pages that are not always current, '
      'international review sites that only cover the famous routes, social media, and '
      'whatever the hotel desk happens to say.</p></div>'
    + '<div class="arrow">&#8644;</div>'
    + '<div class="card fill tint"><h3>And equally on the honest provider</h3>'
      '<p>A licensed guide with ten years of experience has no cheap way of proving it '
      'to somebody who landed an hour ago. So the experienced guide competes on price '
      'with whoever quotes lowest, and loses.</p>'
      '<p>The market ends up punishing exactly the people the 2023 guide rule was '
      'written to protect, which is the second half of the problem and the half that '
      'usually gets left out.</p></div>'
    + '</div></div>'
    + foot("The information gap, from both sides"))


add("fig03_theory", head(
    "Chapter 1 · Theory",
    "Three Ideas That Explain the Market, and What Each One Built",
    "The theory is not decoration on a software project. Each idea explains a "
    "cause, and each one is the reason a specific feature exists.")
    + '<div class="body">'
    + '<div class="grid3">'
    + ''.join(
        f'<div class="col eq">'
        f'<div class="card solid" style="border-top:5px solid {c}">'
        f'<span class="pill" style="background:{bg};color:{c}">{tag}</span>'
        f'<h3 style="margin-top:11px">{t}</h3><p>{d}</p>'
        f'<p style="margin-top:10px;color:#6D766C"><b class="hl">The market symptom.</b> {sym}</p>'
        f'</div>'
        f'<div class="card tint" style="border-left:5px solid {c}">'
        f'<h3 style="font-size:18.6px">&#8595;&nbsp; What GuideU built</h3><p>{feat}</p></div>'
        f'</div>'
        for t, tag, d, sym, feat, c, bg in [
            ("Information asymmetry", "Akerlof, 1970",
             "When a buyer cannot tell good from bad before paying, they only offer an "
             "average price. Good sellers refuse it and leave, quality falls further, and "
             "the market fills up with lemons. Akerlof also gave the cure: signalling by "
             "the seller, and screening by an intermediary. Spence (1973) showed a costly, "
             "observable credential can carry the signal.",
             "A licensed guide and an opportunist make the same claims, so both get "
             "bargained down to the same price.",
             "A verified registry keyed on the NTB licence number is the signalling "
             "device. The price benchmark and the scam-risk score are the screening "
             "devices.", TEAL, "#E1F1F2"),
            ("Bounded rationality", "Simon, 1955",
             "People do not optimise. They have limited time, attention and information, "
             "so they search until something is good enough and then stop. Simon called "
             "it satisficing, and it is a rational response to real limits rather than "
             "laziness. Iyengar and Lepper (2000) showed the other half: too much choice "
             "can stop people choosing at all.",
             "Nobody reads four hundred reviews and cross-checks a licence register. They "
             "ask the hotel desk and book, which is exactly what a scam is built for.",
             "A recommender does the aggregating and filtering a tired traveller cannot "
             "do, and hands back a short list a person can actually work through.",
             INDIGO, "#EAE7F7"),
            ("Choice architecture", "Thaler &amp; Sunstein, 2008",
             "There is no neutral way to present a choice. Whatever sits at the top of a "
             "list, whatever is selected by default, whatever is highlighted, all of it "
             "moves what people pick. Whoever designs the presentation is a choice "
             "architect whether they wanted the job or not.",
             "The moment the platform orders a list of guides it is steering a decision "
             "about somebody's money and sometimes their safety.",
             "Ranking is kept explainable. The reason shown on a card is arithmetic taken "
             "from the model itself, and an expired licence is never out-ranked by a good "
             "predicted match.", AMBER, "#FCF0DC"),
        ])
    + '</div></div>'
    + foot("From economic theory to product decisions"))


add("fig04_data_uses", head(
    "Chapter 1 · Role of data and machine learning",
    "Five Services, and the Problem Each One Is Actually For",
    "Artificial intelligence gets claimed loosely in tourism products, so it is "
    "worth being exact about what each model does and which gap it closes.")
    + '<div class="body">'
    + '<div class="grid5" style="margin-bottom:16px">'
    + ''.join(
        f'<div class="card solid" style="border-top:5px solid {c}">'
        f'<h3 style="font-size:19.8px">{n}</h3>'
        f'<p style="font-size:15.5px"><b class="hl">Does.</b> {does}</p>'
        f'<p style="font-size:15.5px"><b class="hl">Answers.</b> {ans}</p>'
        f'<div style="margin-top:11px"><span class="pill" style="background:{bg};color:{c}">{alg}</span></div>'
        f'</div>'
        for n, does, ans, alg, c, bg in [
            ("Route recommender", "Ranks 2,000 routes for one traveller.",
             "Bounded rationality &mdash; it shortens a search nobody can finish.",
             "Logistic regression", TEAL, "#E1F1F2"),
            ("Anti-scam classifier", "Scores a quoted price as fair or overcharged.",
             "Asymmetry &mdash; a screening device the buyer never had.",
             "Gradient boosting", CRIMSON, "#FBE7E5"),
            ("Guide matching", "Predicts how a traveller and a guide will suit each other.",
             "Asymmetry &mdash; matching instead of sorting by stars.",
             "Ridge regression", INDIGO, "#EAE7F7"),
            ("Arrivals forecast", "Projects monthly arrivals ahead of a season.",
             "Capacity &mdash; so guide supply can be planned, not guessed.",
             "Log-linear OLS", AMBER, "#FCF0DC"),
            ("Tourist segments", "Groups travellers by their survey preferences.",
             "Cold start &mdash; a first-time user needs some starting profile.",
             "K-means, k = 4", "#6B911C", "#EDF7DA"),
        ])
    + '</div>'
    + '<div class="row">'
    + '<div class="card fill dark"><h3>What these models honestly do not do</h3>'
      '<p>None of them detects a scam in the sense of proving intent. The classifier '
      'scores price patterns that resemble previously labelled overcharging, which is a '
      'statistical association and not a judgement about a person.</p>'
      '<p>The benchmark does not know what a service is worth. It knows what comparable '
      'services cost in the data it was shown. The recommender does not know what a '
      'traveller will enjoy; it knows which attributes went with earlier choices.</p></div>'
    + '<div class="card fill tint"><h3>Two rules that governed all five</h3>'
      '<p><b class="hl">Baseline first.</b> Everything runs on simple scikit-learn models, '
      'and heavier machinery only gets used if the data actually justifies it. On this '
      'data it never did.</p>'
      '<p><b class="hl">Temporal split, never random.</b> Every model is tested only on '
      'interactions that happened after the ones it learned from. A random split leaks '
      'the future into training and produces flattering numbers that fall apart on '
      'contact with anything real.</p></div>'
    + '</div></div>'
    + foot("How the platform uses data"))


add("fig05_pipeline", head(
    "Chapter 1 · Method",
    "From Ten CSV Files to a Prediction on a Phone",
    "One pipeline serves all five models, and the evaluation protocol is fixed "
    "at the start rather than chosen after seeing the numbers.")
    + '<div class="body">'
    + '<div class="row" style="align-items:stretch;margin-bottom:18px">'
    + ''.join(
        (f'<div class="card solid fill" style="border-top:5px solid {c}">'
         f'<span class="pill" style="background:{bg};color:{c}">Step {i}</span>'
         f'<h3 style="margin-top:10px;font-size:19.8px">{t}</h3><p style="font-size:15.5px">{d}</p></div>')
        + ('<div class="arrow">&#8594;</div>' if i < 5 else '')
        for i, (t, d, c, bg) in enumerate([
            ("Load and cache", "Ten CSV files read once and held in memory. Dates parsed "
             "on load and a year column derived, because every model splits on it.", TEAL, "#E1F1F2"),
            ("Profile first", "Check every relationship the documentation claims before "
             "building anything. Half of them turned out not to exist.", AMBER, "#FCF0DC"),
            ("Engineer features", "Normalise route attributes to 0&ndash;1 so coefficients "
             "stay comparable, build the tourist-route gap terms, sample negatives.", INDIGO, "#EAE7F7"),
            ("Train and select", "Fit on 2021&ndash;2023. Choose the model and the "
             "threshold on 2023 only, before the test year is opened.", "#6B911C", "#EDF7DA"),
            ("Score and serve", "Register the artifact with its model card, then serve it "
             "over HTTP with a fallback behind it.", CRIMSON, "#FBE7E5"),
        ], start=1))
    + '</div>'
    + '<div class="row">'
    + '<div class="card fill"><h3>The split, and why it is not random</h3>'
      '<div style="display:flex;gap:8px;margin:14px 0 12px">'
      f'<div style="flex:3;background:{TEAL};color:#fff;border-radius:9px;padding:13px;text-align:center">'
      '<b style="font-size:21.1px">2021 &ndash; 2023</b><br><span style="font-size:14.9px">TRAIN</span></div>'
      f'<div style="flex:1;background:{AMBER};color:#fff;border-radius:9px;padding:13px;text-align:center">'
      '<b style="font-size:21.1px">2023</b><br><span style="font-size:14.9px">VALIDATE</span></div>'
      f'<div style="flex:1;background:{CRIMSON};color:#fff;border-radius:9px;padding:13px;text-align:center">'
      '<b style="font-size:21.1px">2024</b><br><span style="font-size:14.9px">TEST</span></div>'
      '</div>'
      '<p>Model choice and any decision threshold are fixed on the validation year, so the '
      'operating point reported is never tuned on the data it is reported against. The '
      'test year is opened once, at the end.</p></div>'
    + '<div class="card fill tint"><h3>Every number has a comparator</h3>'
      '<p>Twelve baselines are scored through the same harness on the same split: random '
      'and popularity for ranking, the majority class for classification, seasonal naive '
      'and its growth-scaled version for forecasting, the global mean and the guide\'s own '
      'star rating for regression.</p>'
      '<p>A precision figure with no baseline beside it has not answered anything. That is '
      'the reason the phrase "against sensible baselines" is written into the research '
      'question itself.</p></div>'
    + '</div></div>'
    + foot("The machine learning pipeline and evaluation protocol"))



# ==========================================================================
# CHAPTER 2 — RESEARCH DESIGN
# ==========================================================================
add("fig06_aim", head(
    "Chapter 2 · Research aim",
    "The Aim of This Project, in One Statement",
    "")
    + '<div class="body">'
    + '<div class="card dark" style="padding:30px 34px;margin-bottom:18px">'
      '<p style="font-size:27.3px;line-height:1.5;color:#F0F6E4">To design, build and '
      'honestly evaluate a <b style="color:#C8E58A">mobile-first travel platform for '
      'Nepal</b> that uses machine learning on real travel-planning data to reduce the '
      'information gap between tourists and informal-sector providers &mdash; and to '
      'report exactly how far that works, including where it does not.</p></div>'
    + '<div class="grid4" style="margin-bottom:16px">'
    + ''.join(
        f'<div class="card solid" style="border-top:5px solid {c}">'
        f'<div class="num" style="background:{c};margin-bottom:11px">{i}</div>'
        f'<h3 style="font-size:19.8px">{t}</h3><p style="font-size:15.5px">{d}</p></div>'
        for i, (t, d, c) in enumerate([
            ("Reduce the gap, not remove it",
             "Objective criteria where objective criteria exist. No claim to be an oracle "
             "about somebody's holiday.", TEAL),
            ("Build the thing, then measure it",
             "The gap in the literature is one of integration, and that can only be "
             "answered by building the combination and scoring it.", "#6B911C"),
            ("Protect both sides of the market",
             "Tourists from overcharging, and guides from the platform's own price "
             "transparency pushing their pay down.", AMBER),
            ("Report the failures too",
             "A model that produced nothing useful is kept in the report, because knowing "
             "which one is weak is worth more than five tidy successes.", CRIMSON),
        ], start=1))
    + '</div>'
    + '<div class="card tint"><p style="font-size:18.0px">The aim deliberately contains '
      'two halves. The first half is ordinary engineering, and plenty of student projects '
      'do it. The second half &mdash; reporting honestly how far it works &mdash; turned '
      'out to be where most of the contribution actually sits, because five models on the '
      'same data succeeded very unevenly and the pattern in that unevenness is the useful '
      'finding.</p></div>'
    + '</div>'
    + foot("The research aim"))


add("fig07_objectives", head(
    "Chapter 2 · Research objectives",
    "Six Objectives, and What Each One Delivered",
    "Set at proposal stage, checked at the end. Each objective produced "
    "something that can be pointed at in the repository.")
    + '<div class="body"><div class="grid3">'
    + ''.join(
        f'<div class="card solid" style="border-left:6px solid {c}">'
        f'<div style="display:flex;align-items:center;gap:11px;margin-bottom:9px">'
        f'<div class="num" style="background:{c}">O{i}</div>'
        f'<h3 style="margin:0;font-size:20.5px">{t}</h3></div>'
        f'<p style="font-size:16.1px">{d}</p>'
        f'<div style="margin-top:12px;padding-top:10px;border-top:1px dashed #DCE3D2">'
        f'<span class="pill ok">Delivered</span> '
        f'<span style="font-size:15.5px;color:#5A655C">{ev}</span></div></div>'
        for i, (t, d, ev, c) in enumerate([
            ("Review the ground",
             "Read the recommender, review-mining, trust and AI-ethics literature critically, "
             "and find the specific gap rather than summarising four fields.",
             "Chapter 4, 4 platform case studies, 54 sources", TEAL),
            ("Profile the data first",
             "Test every relationship the dataset documentation claims before committing to "
             "any model design.",
             "Half the claimed signals found to be absent", AMBER),
            ("Build the platform",
             "A working multi-service system across five agile sprints, not a notebook with "
             "a demo attached.",
             "5 services, 5 sprints, all merged to main", INDIGO),
            ("Train and evaluate models",
             "Fit real models on the travel-planning data and score every one against a "
             "sensible baseline on a temporal split.",
             "5 models, 12 baselines, test year 2024", "#6B911C"),
            ("Design fairness in, then audit it",
             "Put concrete protections in the code for both sides of the market, then check "
             "whether they actually worked.",
             "Fair-wage rule in 2 services, per-continent audit", CRIMSON),
            ("Report it honestly",
             "Document what was deferred, what failed, and what the evidence cannot "
             "support, at the same length as the successes.",
             "Negative results, 10 defects, threats to validity", SLATE),
        ], start=1))
    + '</div></div>'
    + foot("The six research objectives"))


add("fig08_questions", head(
    "Chapter 2 · Research questions",
    "Two Questions: One Technical, One Ethical",
    "The wording matters. Both questions were written before any model was "
    "trained, and neither was adjusted afterwards to fit the numbers.")
    + '<div class="body"><div class="grid2">'
    + ''.join(
        f'<div class="card solid" style="border-top:6px solid {c}">'
        f'<span class="pill" style="background:{bg};color:{c}">{tag}</span>'
        f'<h3 style="margin-top:12px;font-size:23.6px">{t}</h3>'
        f'<p style="font-size:18.0px;color:#2C3B22;line-height:1.6">{q}</p>'
        f'<div class="vsep"></div>'
        f'<p style="font-size:16.1px"><b class="hl">Why it is worded that way.</b> {why}</p>'
        f'<p style="font-size:16.1px"><b class="hl">How it gets answered.</b> {how}</p></div>'
        for t, tag, q, why, how, c, bg in [
            ("RQ1 &mdash; Technical", "Measurable",
             "&ldquo;To what extent can machine-learning services &mdash; a personalised "
             "recommender together with price-benchmarking and scam-risk models &mdash; "
             "provide accurate and useful decision support for tourists planning travel in "
             "Nepal, when evaluated against sensible baselines on the project dataset using "
             "a temporal split?&rdquo;",
             "The phrase <em>against sensible baselines</em> is deliberate. A recommender "
             "reporting precision at five without saying what a non-personalised list would "
             "have scored has not answered anything, and the same goes for a classifier with "
             "no majority-class comparator.",
             "Five models scored against twelve baselines through the same harness, on the "
             "same 2024 test year, with model selection done on 2023.", TEAL, "#E1F1F2"),
            ("RQ2 &mdash; Ethical", "Reflective",
             "&ldquo;What ethical risks arise when an AI-driven platform mediates trust "
             "between tourists and informal-sector providers, and how effectively can those "
             "risks be mitigated within the design of such a platform?&rdquo;",
             "It asks about mitigation <em>within the design</em>, which keeps the question "
             "answerable. The project cannot fix discrimination in Nepal's guide market; it "
             "can only report what its own design does and does not do about it.",
             "A per-continent fairness audit of the anti-scam model, a working provider-side "
             "protection with tests, and one identified risk the project could not solve.",
             INDIGO, "#EAE7F7"),
        ])
    + '</div></div>'
    + foot("The two research questions"))


add("fig09_hypotheses", head(
    "Chapter 2 · Research hypotheses",
    "Three Hypotheses, Set Before Any Model Was Trained",
    "Each one carries a target taken from published work rather than a number "
    "invented to be easy to hit.")
    + '<div class="body">'
    + ''.join(
        f'<div class="card solid" style="border-left:6px solid {c};margin-bottom:14px">'
        f'<div style="display:flex;gap:20px;align-items:center">'
        f'<div style="flex:none;width:96px;text-align:center">'
        f'<div style="font-size:37.2px;font-weight:700;color:{c}">{h}</div>'
        f'<span class="pill {v[1]}" style="margin-top:7px">{v[0]}</span></div>'
        f'<div style="flex:1"><h3 style="font-size:20.5px">{t}</h3><p>{d}</p></div>'
        f'<div style="flex:none;width:330px;background:#F4F8EC;border-radius:11px;padding:14px 16px">'
        f'<p style="font-size:15.5px"><b class="hl">Where the target came from.</b> {src}</p></div>'
        f'</div></div>'
        for h, t, d, src, v, c in [
            ("H1", "Personalisation will beat a popularity baseline by a practically "
             "meaningful margin",
             "Measured on hit-rate at ten over the 2024 test year, against a "
             "non-personalised popularity ranking scored through the same harness. Result: "
             "0.0135 against 0.0083, a lift of 1.63 times.",
             "The recommender literature consistently finds personalisation beats popularity "
             "once even modest user signal exists (Adomavicius &amp; Tuzhilin, 2005), though "
             "Cremonesi et al. (2010) warn popularity is a far stronger comparator than most "
             "papers admit.", ("Supported", "ok"), TEAL),
            ("H2", "The scam-risk model will reach at least 90% accuracy or F1 on held-out "
             "data",
             "Enough to support a usable risk signal at provider level. Result: 99.1% "
             "accuracy and F1 0.980 on 2024, holding at F1 0.958 on sixty service and "
             "region combinations the model had never seen.",
             "Deception-detection work found automated classifiers reaching roughly ninety "
             "per cent on review text while human judges performed close to chance (Ott et "
             "al., 2011).", ("Supported", "ok"), "#6B911C"),
            ("H3", "Fairness-aware adjustments can be applied without a large loss in "
             "predictive usefulness",
             "The hypothesis that matters most for RQ2, because if fairness and accuracy "
             "trade off badly then ethical design carries a real cost that has to be "
             "reported rather than assumed away.",
             "Supported for what was implemented, but by a weaker test than the wording "
             "implies. Excluding protected attributes cost almost nothing; no intervention "
             "that genuinely trades against the objective was applied.",
             ("Supported, weakly", "mid"), AMBER),
        ])
    + '</div>'
    + foot("The three research hypotheses and their verdicts"))


add("fig10_claims", head(
    "Chapter 2 · Contribution",
    "What This Thesis Claims, and What It Deliberately Does Not",
    "An overstated contribution is easy to take apart in a viva. A narrow one "
    "that the evidence actually supports is worth more.")
    + '<div class="body"><div class="grid2">'
    + '<div class="card solid" style="border-top:6px solid #6B911C">'
      '<span class="pill ok">Claimed</span>'
      '<h3 style="margin-top:12px">Three things, and no more</h3>'
    + ''.join(
        f'<div style="display:flex;gap:12px;margin-top:14px">'
        f'<div class="num" style="background:#6B911C">{i}</div>'
        f'<div><b class="hl">{t}</b><p style="font-size:16.1px;margin-top:3px">{d}</p></div></div>'
        for i, (t, d) in enumerate([
            ("Academic", "An empirical case study of recommendation, benchmarking and risk "
             "scoring in a low-resource informal market. Almost all recommender evidence "
             "comes from dense Western platforms; this is the opposite case."),
            ("Practical", "A working multi-service prototype in a sector the Nepali "
             "government has named a strategic priority, in a regulatory setting where "
             "choosing a guide is now compulsory."),
            ("Methodological", "An honest account of agile development under real "
             "constraints, including the features deliberately dropped, the models that did "
             "not work, and ten defects a green test suite never caught."),
        ], start=1))
    + '</div>'
    + '<div class="card solid" style="border-top:6px solid #C0392B">'
      '<span class="pill no">Not claimed</span>'
      '<h3 style="margin-top:12px">Four things this evidence cannot support</h3>'
    + ''.join(
        f'<div style="display:flex;gap:12px;margin-top:14px">'
        f'<div class="num" style="background:#C0392B">&times;</div>'
        f'<div><b class="hl">{t}</b><p style="font-size:16.1px;margin-top:3px">{d}</p></div></div>'
        for t, d in [
            ("A new algorithm", "Every technique here is drawn from established literature "
             "and applied. The value is in the integration, not in novelty."),
            ("That GuideU reduces scams in Nepal", "That would need real users, real "
             "transactions and a longitudinal study far beyond a final-year project."),
            ("Real-world accuracy", "All five models are trained on synthetic data. The "
             "pipeline is demonstrably correct; the numbers describe a generated world."),
            ("Solved ethics", "One risk &mdash; the discrimination surface that verification "
             "itself creates &mdash; was identified and could not be fixed. It is recorded "
             "as an open problem."),
        ])
    + '</div></div>'
    + '<div class="card tint" style="margin-top:16px"><p style="font-size:17.4px">'
      'What survives those subtractions is still worth something. A working integration '
      'exists where before there was only an argument that one should exist, the trade-offs '
      'are documented rather than hidden, and the ethical risks are named specifically '
      'including the one that has no answer yet.</p></div>'
    + '</div>'
    + foot("The scope of the contribution"))


# ==========================================================================
# CHAPTER 3 — METHODOLOGY AND ETHICS
# ==========================================================================
add("fig11_methodology", head(
    "Chapter 3 · Methodology",
    "A Desk Study and a Build, Working on Each Other",
    "The research question is whether known techniques can be integrated for a "
    "new setting, which needs careful reading and then an artefact.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill solid" style="border-top:5px solid ' + TEAL + '">'
      '<h3>Desk-based research</h3>'
      '<p>Academic journals, tourism reports, government publications and reputable '
      'industry sources on travel platforms, recommenders, review mining, digital trust '
      'and AI ethics. Secondary data rather than primary field surveys, which is realistic '
      'for a final-year project and is also a stated limitation.</p>'
      '<div class="vsep"></div>'
      '<p style="font-size:15.5px"><b class="hl">Selection rule.</b> Peer-reviewed work for '
      'anything making a causal or empirical claim. Industry and government sources only '
      'for factual figures such as arrival counts, where they are the primary record. News '
      'reporting only for events, never for effects. Anything that could not be traced to a '
      'source I could actually read was dropped rather than cited second hand.</p></div>'
    + '<div class="card fill solid" style="border-top:5px solid #6B911C">'
      '<h3>Agile build and evaluate</h3>'
      '<p>Five sprints following the values of the Agile Manifesto and the sprint structure '
      'of the Scrum Guide. Agile fits because the requirements really were uncertain at the '
      'start, and understanding of both the data and the architecture improved with every '
      'iteration.</p>'
      '<div class="vsep"></div>'
      '<p style="font-size:15.5px"><b class="hl">Version control mirrors the process.</b> '
      'One long-lived branch per sprint plus main, each merged with a no-fast-forward '
      'release merge so the history shows discrete increments rather than one flat run of '
      'commits.</p></div>'
    + '<div class="card fill solid" style="border-top:5px solid ' + AMBER + '">'
      '<h3>Requirements, from three sources</h3>'
      '<p><b class="hl">1.</b> The problem analysis in the proposal &mdash; fragmented '
      'booking, scam and overpricing risk, safety around unverified guides.</p>'
      '<p><b class="hl">2.</b> The case-study evidence in Chapter 4, which showed which '
      'trust mechanisms actually work on comparable platforms and which do not.</p>'
      '<p><b class="hl">3.</b> The regulatory environment, particularly the 2023 mandatory '
      'guide rule, which turned guide discovery from a convenience into a necessity.</p></div>'
    + '</div>'
    + '<div class="card dark"><h3>One honest methodological point</h3>'
      '<p>The planning documents and the delivered system diverged, as they usually do in '
      'real agile work. The sprint board described an aspirational plan; the per-sprint '
      'review documents recorded what was actually delivered. Where the two disagree this '
      'thesis treats the reviews and the code as the authoritative record. Reporting that '
      'divergence is part of the contribution, not an admission of failure.</p></div>'
    + '</div>'
    + foot("The research methodology"))


add("fig12_sprints", head(
    "Chapter 3 · Agile delivery",
    "Five Sprints, and the Scope Calls That Made Them Fit",
    "Every sprint branch was merged into main with a release merge. The machine "
    "learning work came afterwards and was distributed back across the same "
    "five branches by theme.")
    + '<div class="body">'
    + '<div class="row" style="gap:12px;margin-bottom:18px">'
    + ''.join(
        f'<div class="card fill solid" style="border-top:5px solid {c}">'
        f'<div style="display:flex;align-items:center;gap:9px;margin-bottom:9px">'
        f'<div class="num" style="background:{c};width:26px;height:26px;font-size:16.1px">{i}</div>'
        f'<b style="font-size:18.6px;color:#3E5514">{t}</b></div>'
        f'<p style="font-size:15.5px">{d}</p>'
        f'<div style="margin-top:11px"><span class="pill ink">ML added later: {ml}</span></div>'
        f'</div>'
        for i, (t, d, ml, c) in enumerate([
            ("Foundation", "Monorepo, service skeletons, Docker Compose, Nginx, MLflow, "
             "CI per deployable unit, architecture and data documentation.",
             "data loaders", TEAL),
            ("Discovery", "JWT authentication, mobile shell and navigation, dataset-backed "
             "destination browsing, verified-guide listing and profiles.",
             "anti-scam", "#00A0A8"),
            ("Marketplace", "Package-centric bookings scoped to the requesting user, "
             "simulated eSewa and Khalti payments, ratings and reviews with moderation.",
             "guide matching", "#6B911C"),
            ("AI and chat", "Recommendation feeds with fallbacks, fair-price checks, "
             "festival calendar, JWT-authenticated live chat, read-only admin dashboard.",
             "recommender", AMBER),
            ("Product and deploy", "Travel workspaces and budgets, currency conversion, SOS "
             "alerts, throttling and sanitisation, end-to-end journey tests, production "
             "Compose.", "forecast, segments", CRIMSON),
        ], start=1))
    + '</div>'
    + '<div class="row">'
    + '<div class="card fill"><h3>MoSCoW, and what it actually did</h3>'
      '<table class="t" style="margin-top:8px"><tr><th>Priority</th><th>Items</th>'
      '<th style="width:150px">Outcome</th></tr>'
      '<tr><td><span class="pill">Must</span></td><td>Verified guide profiles, destination '
      'discovery, bookings, the recommendation service</td>'
      '<td style="color:#1F6B34;font-weight:600">All shipped</td></tr>'
      '<tr><td><span class="pill mid">Should</span></td><td>Chat, travel workspace, currency '
      'conversion, safety and SOS</td>'
      '<td style="color:#1F6B34;font-weight:600">All shipped</td></tr>'
      '<tr><td><span class="pill no">Could</span></td><td>Gateway cryptographic '
      'verification, authenticated admin login, wider dashboard write actions</td>'
      '<td style="color:#9A2F26;font-weight:600">Dropped</td></tr></table>'
      '<p style="margin-top:11px;font-size:16.1px">The could-haves are exactly the items that '
      'fell away when time ran short. That is not an accident, it is the prioritisation '
      'working. A project this size with one developer either prioritises honestly or fails '
      'everywhere at once.</p></div>'
    + '<div class="card tint" style="width:430px"><h3>Why the ML went back across the branches</h3>'
      '<p>The machine-learning phase happened after the fifth sprint closed. Rather than '
      'open a sixth branch that fitted no part of the narrative, each piece of work was '
      'placed on the sprint whose theme it belonged to, synchronised from main, committed, '
      'pushed and merged back.</p>'
      '<p>That kept one consistent history and meant every merge could be verified on its '
      'own.</p></div>'
    + '</div></div>'
    + foot("Agile sprint history and the scope decisions"))


add("fig13_ethics", head(
    "Chapter 3 · Ethics",
    "Five Ethical Risks, and the Line of Code Each One Produced",
    "Ethics is treated as a continuous design concern here rather than a form "
    "filled in at the end, so every entry below names something concrete.")
    + '<div class="body">'
    + '<table class="t"><tr><th style="width:220px">Risk</th><th style="width:330px">Why it matters here</th>'
      '<th>What was actually built</th><th style="width:150px">Status</th></tr>'
    + ''.join(
        f'<tr><td><b class="hl">{r}</b></td><td>{w}</td><td>{b}</td>'
        f'<td><span class="pill {sc}">{st}</span></td></tr>'
        for r, w, b, st, sc in [
            ("Privacy and data protection",
             "Location, preferences and booking history are personal data by any reasonable "
             "definition, and trust in tech companies with data is already low.",
             "Data minimisation and purpose limitation per the GDPR, user access and "
             "deletion, and Nepal's Individual Privacy Act 2075 as the local floor.",
             "Implemented", "ok"),
            ("Unfair harm to a guide",
             "In a market where reputation is income, a wrong risk score is a livelihood "
             "problem and not an inconvenience.",
             "Nationality and continent are never model inputs, a per-continent audit runs "
             "after training, and a disparity gate routes the model to review.",
             "Implemented", "ok"),
            ("Transparency eroding wages",
             "Publishing a fair range helps a tourist spot an overcharge and equally helps "
             "them anchor every negotiation at the floor of it.",
             "A below-fair-wage flag on labour services, enforced independently in two "
             "services, with tests in both and its own colour in the app.",
             "Implemented", "ok"),
            ("Ranking as manipulation",
             "The difference between a helpful ranking and a manipulative one is invisible "
             "to the person looking at it.",
             "The recommender stayed a linear model so the reason on a card is arithmetic "
             "from the ranking itself, and verification can never be out-ranked.",
             "Implemented", "ok"),
            ("Verification creating a discrimination surface",
             "Any system that surfaces provider identity to build trust also creates a "
             "surface on which discrimination can act.",
             "Credentials are surfaced rather than photographs, which narrows the surface. "
             "A guide's name still carries ethnic and caste information in Nepal.",
             "Open problem", "no"),
        ])
    + '</table>'
    + '<div class="row" style="margin-top:16px">'
    + '<div class="card fill tint"><h3>Ethics of the research process</h3>'
      '<p>Desk-based methodology, no primary data from human participants, so no participant '
      'consent or withdrawal machinery was needed. If the user study proposed in the '
      'conclusion ever runs it would need institutional approval, informed consent, the '
      'right to withdraw and anonymised storage, and none of that is optional.</p></div>'
    + '<div class="card fill dark"><h3>Why synthetic data was an ethical choice too</h3>'
      '<p>The obvious alternative was scraping reviews and guide profiles from existing '
      'platforms. That processes real people\'s identities and livelihoods without their '
      'knowledge and usually against the source platform\'s terms. Given that the whole '
      'argument of this thesis is about fairness toward providers, harvesting those same '
      'providers\' data without asking would have been an obvious contradiction. The price '
      'paid is external validity, and it is a real one.</p></div>'
    + '</div></div>'
    + foot("Ethical risks and the design decision each one produced"))



# ==========================================================================
# CHAPTER 4 — LITERATURE REVIEW
# ==========================================================================
add("fig14_lit_map", head(
    "Chapter 4 · Literature synthesis",
    "Four Mature Fields, and the Hole Where They Should Meet",
    "Each strand is well developed on its own. What is missing is their "
    "combination for a sparse, informal, pre-launch market.")
    + '<div class="body">'
    + '<div class="grid4" style="margin-bottom:18px">'
    + ''.join(
        f'<div class="card solid" style="border-top:5px solid {c}">'
        f'<h3 style="font-size:19.8px">{t}</h3>'
        f'<p style="font-size:15.5px">{d}</p>'
        f'<div class="vsep"></div>'
        f'<p style="font-size:14.9px;color:#6D766C"><b class="hl">Key warning.</b> {w}</p></div>'
        for t, d, w, c in [
            ("Recommender systems",
             "Collaborative, content-based and hybrid families are well mapped. The cold "
             "start problem has known remedies and ranking metrics are standardised.",
             "Ferrari Dacrema et al. (2019) reproduced eighteen neural papers and found "
             "tuned simple baselines beat most of them. Popularity is a much harder "
             "comparator than papers admit.", TEAL),
            ("Review mining and deception",
             "Deception in review text is machine-detectable at roughly ninety per cent "
             "where humans perform near chance, and spam leaves duplicate patterns.",
             "A quoted price is a number and not a text, so the analogue is imperfect. What "
             "carries over is the principle that deception leaves statistical traces.", AMBER),
            ("Trust and asymmetry online",
             "Verification, held payment and human signals explain platform trust better "
             "than raw ratings do, across several independent studies.",
             "Ert et al. (2016) found host photos drove price while review scores did not. "
             "Edelman et al. (2017) then showed identity display enables discrimination.", INDIGO),
            ("Algorithmic ethics and fairness",
             "Impossibility results, multi-sided fairness and the interpretability debate "
             "all give concrete guardrails rather than slogans.",
             "Chouldechova (2017) proved calibration and error-rate balance cannot both hold "
             "when base rates differ. \"Make it fair\" is not a well-defined instruction.", CRIMSON),
        ])
    + '</div>'
    + '<div class="row">'
    + '<div class="card fill dark"><h3>The gap, stated precisely</h3>'
      '<p>Almost all recommender evidence comes from dense Western platforms with millions '
      'of interactions. There is very little published work on what these techniques do when '
      'the interaction matrix is as thin as an informal, pre-launch market makes it.</p>'
      '<p>And fairness research on recommenders is overwhelmingly about users. Ekstrand et '
      'al. (2022) explicitly note the shortage of work on the producer side, where a '
      'concrete implemented mechanism rather than a proposal is worth something.</p></div>'
    + '<div class="card fill tint"><h3>What this project puts into that gap</h3>'
      '<p><b class="hl">A data point on sparsity.</b> The interaction data here could not '
      'support collaborative filtering at all, and one content signal carried essentially '
      'the entire model. That is measured rather than asserted.</p>'
      '<p><b class="hl">A provider-side protection that exists in code.</b> The '
      'below-fair-wage flag runs in two services with tests in both, rather than being '
      'proposed as future work.</p>'
      '<p><b class="hl">A candid account of what broke.</b> Including ten defects that a '
      'passing test suite never caught.</p></div>'
    + '</div></div>'
    + foot("The four literature strands and the gap between them"))


add("fig15_cf_ruled_out", head(
    "Chapter 4 · Method selection",
    "Why Collaborative Filtering Was Ruled Out by Measurement",
    "The comfortable move would be to avoid matrix factorisation for lack of "
    "time. It was tested instead, and the data said no.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill"><h3>What the interaction matrix actually looks like</h3>'
      '<div class="bars" style="margin-top:14px">'
    + bar("Users with interactions", 100, "33,154", TEAL)
    + bar("Items in the catalog", 100, "2,000", SLATE)
    + bar("Matrix density", 4, "0.00106", CRIMSON, "essentially empty")
    + bar("Positives per user", 12, "1.15", CRIMSON, "mean")
    + bar("Users with &gt; 1 positive", 14, "13.5%", AMBER, "1,398 of 10,344")
    + '</div>'
      '<p style="margin-top:14px;font-size:16.1px">At 1.15 positive events per user there is '
      'almost no co-occurrence for user-user or item-item similarity to work with. Nearest '
      'neighbours have no neighbours.</p></div>'
    + '<div class="card fill tint"><h3>The test that settled it</h3>'
      '<p>Rather than assume history was useless, it was checked directly: does a user\'s '
      'own 2021&ndash;2023 region history predict the region they book in 2024?</p>'
      '<div style="display:flex;gap:14px;margin:16px 0 6px">'
      f'<div class="stat r" style="flex:1"><b>23.3%</b><span>using the user\'s own<br>region history</span></div>'
      f'<div class="stat" style="flex:1"><b>36.9%</b><span>just guessing the most<br>popular region</span></div>'
      '</div>'
      '<p style="margin-top:12px;font-size:16.7px"><b class="hl">Using a user\'s history is '
      'worse than ignoring it.</b> That is a stronger and more defensible reason to skip '
      'matrix factorisation than saying there was not enough time, and it lines up with '
      'Ferrari Dacrema et al. (2019) on tuned simple baselines.</p></div>'
    + '</div>'
    + '<div class="card solid"><h3>What was used instead, and why it fits</h3>'
      '<div class="grid3" style="margin-top:12px">'
      '<div><b class="hl">Content and profile features</b><p style="font-size:15.5px">Route '
      'attributes and tourist survey scores need no interaction history at all, so the cold '
      'start problem does not apply to them.</p></div>'
      '<div><b class="hl">Cross terms, not raw pairs</b><p style="font-size:15.5px">Giving '
      'the model the gap between what a tourist wants and what a route offers lets a linear '
      'model capture an interaction that would otherwise need a non-linear one.</p></div>'
      '<div><b class="hl">Popularity as the only collaborative term</b>'
      '<p style="font-size:15.5px">Computed from the training period only, so no test-period '
      'information leaks in. It ended up as the second-largest coefficient.</p></div>'
      '</div></div>'
    + '</div>'
    + foot("Why collaborative filtering was rejected on evidence"))


add("fig16_case_studies", head(
    "Chapter 4 · Platform case studies",
    "Four Platforms, and the Lesson Taken From Each",
    "Chosen deliberately rather than for convenience: two that show trust "
    "working and failing at scale, one pair in a comparable market, and Nepal's "
    "own most recent attempt.")
    + '<div class="body"><div class="grid4">'
    + ''.join(
        f'<div class="col eq"><div class="card solid" style="border-top:5px solid {c}">'
        f'<h3 style="font-size:20.5px">{n}</h3>'
        f'<span class="pill" style="background:{bg};color:{c}">{tag}</span>'
        f'<p style="font-size:15.5px;margin-top:11px">{d}</p>'
        f'<div class="vsep"></div>'
        f'<p style="font-size:15.5px"><b class="hl">The uncomfortable finding.</b> {u}</p></div>'
        f'<div class="card tint" style="border-left:5px solid {c}">'
        f'<p style="font-size:15.5px"><b class="hl">What GuideU took from it.</b> {took}</p></div></div>'
        for n, tag, d, u, took, c, bg in [
            ("Airbnb", "Trust at scale",
             "The clearest case of a platform manufacturing trust between strangers. "
             "Verification and payment held until check-in removed the largest risk from "
             "the guest side.",
             "Ert et al. (2016) found a host's photo predicted price and booking probability "
             "while their review score did not. Edelman et al. (2017) then found guests with "
             "distinctively African-American names were about sixteen per cent less likely "
             "to be accepted.",
             "Surface credentials, not photographs. It narrows the discrimination surface "
             "without pretending to close it, and the residual risk is reported.", CRIMSON, "#FBE7E5"),
            ("TripAdvisor", "User content",
             "The dominant source of user-generated travel content, so the natural "
             "comparator for any travel information platform. Its strengths are scale and "
             "coverage.",
             "Ranking depends on review volume, so popular places accumulate reviews, rank "
             "higher and get more popular. For Nepal that concentrates everything on a few "
             "famous routes.",
             "The gap is not better reviews. TripAdvisor cannot tell you whether a quoted "
             "price is reasonable or whether a guide is licensed, and those are the two "
             "things this market needs most.", AMBER, "#FCF0DC"),
            ("Pathao &amp; InDrive", "Same market",
             "Ride-hailing and delivery across South Asian cities including Kathmandu, with "
             "a largely informal supply side and users often new to digital payment.",
             "Heeks (2017) and Graham et al. (2017) both find platforms in developing "
             "economies can reproduce existing inequalities even while expanding access, "
             "with oversupply pushing pay down.",
             "Keep the supply-side barrier low &mdash; key the registry on the NTB licence a "
             "working guide already has. And support negotiation with a benchmark rather "
             "than replacing it with a fixed price.", TEAL, "#E1F1F2"),
            ("Visit Nepal 2020", "National campaign",
             "The government's flagship tourism campaign, targeting two million visitors. "
             "Suspended in March 2020, so it cannot be judged on whether it hit the target.",
             "Its digital output was a promotional site and social media. No verified "
             "provider registry, no price transparency, no structured open data anybody "
             "could build on.",
             "The constraint was never only demand. Bringing two million visitors into a "
             "market where they cannot check a guide or a price does not obviously improve "
             "anybody's trip.", INDIGO, "#EAE7F7"),
        ])
    + '</div></div>'
    + foot("The four platform case studies"))


# ==========================================================================
# CHAPTER 5 — TECHNICAL DEVELOPMENT
# ==========================================================================
add("fig17_stack", head(
    "Chapter 5 · Tools and technologies",
    "Five Deployable Units, Two Languages, One Monorepo",
    "Each service uses the runtime that suits its workload, and each one ships "
    "on its own without waiting for the others.")
    + '<div class="body">'
    + '<div class="grid5" style="margin-bottom:16px">'
    + ''.join(
        f'<div class="card solid" style="border-top:5px solid {c}">'
        f'<h3 style="font-size:19.8px">{n}</h3>'
        f'<div style="margin:8px 0 10px"><span class="pill" style="background:{bg};color:{c}">{port}</span></div>'
        f'<p style="font-size:15.5px">{d}</p>'
        f'<div class="vsep"></div>'
        f'<p style="font-size:14.9px;color:#6D766C">{libs}</p></div>'
        for n, port, d, libs, c, bg in [
            ("core-engine", "Django · :8000",
             "Owns the catalog, accounts, bookings, payments, reviews, chat history and "
             "every user-facing write. The authoritative record.",
             "Django REST Framework · SimpleJWT · Celery · PostgreSQL in production, SQLite "
             "for local runs", "#6B911C", "#EDF7DA"),
            ("analytics-engine", "FastAPI · :8001",
             "Every machine-learning model. Completely stateless &mdash; it never touches "
             "the database and is handed everything it needs in the request body.",
             "pandas · NumPy · scikit-learn · joblib artifacts · JSON model registry", TEAL, "#E1F1F2"),
            ("real-time-engine", "Node + TS · :8002",
             "Socket.IO transport for live chat and booking status. Verifies the same JWT "
             "on the handshake, then persists each delivered message through the core API.",
             "Express · Socket.IO · TypeScript · Redis pub/sub, optional", INDIGO, "#EAE7F7"),
            ("mobile_app", "Flutter",
             "The traveller's client. One codebase for Android and iOS, which is the only "
             "realistic option for a single developer in an Android-heavy market.",
             "Riverpod · go_router · Dio · socket_io_client · clean architecture per feature",
             AMBER, "#FCF0DC"),
            ("web_admin", "Next.js · :3000",
             "The operator console. Every protected read happens server-side so the ML key "
             "and the staff token never reach the browser bundle.",
             "App Router · React Server Components · shadcn/ui on Base UI · Server Actions",
             CRIMSON, "#FBE7E5"),
        ])
    + '</div>'
    + '<div class="row">'
    + '<div class="card fill"><h3>Why the ML lives in its own service</h3>'
      '<p>A single Django application would have been simpler, so this needs a reason. '
      'Three of them.</p>'
      '<p><b class="hl">Different dependency sets.</b> The ML service needs scikit-learn and '
      'pandas and the web application does not, so keeping them apart keeps both images '
      'smaller and both deployments independent.</p>'
      '<p><b class="hl">Independent scaling.</b> Model loading is the slowest thing the '
      'platform does, and it should not restart the transactional system.</p>'
      '<p><b class="hl">A forced contract.</b> An HTTP boundary makes the ML have defined '
      'inputs and outputs, which is far easier to test and reason about than a function '
      'call buried inside a view.</p></div>'
    + '<div class="card fill tint"><h3>And what that decision cost</h3>'
      '<p>An extra network hop that can fail, and it did. Two of the ten defects found later '
      'came straight out of this boundary: the two services disagreed on the default API key '
      'so every ML call was rejected, and the fallback path was good enough that nobody '
      'noticed for weeks.</p>'
      '<p>The supporting infrastructure is Docker Compose, Nginx as the reverse proxy, Redis '
      'for cache and pub/sub, and MLflow-style artifact registration. Five GitHub Actions '
      'workflows run one per deployable unit on every push.</p></div>'
    + '</div></div>'
    + foot("The technology stack"))


add("fig18_architecture", head(
    "Chapter 5 · System architecture",
    "How the Services Fit Together, and Where Each Model Sits",
    "Clients talk only to the core engine and the socket server. The ML service "
    "is internal, stateless and always has something behind it.")
    + '<div class="body">'
    + '<div class="row" style="align-items:stretch;margin-bottom:16px">'
    + '<div class="col" style="width:250px">'
      '<div class="card solid" style="border-top:5px solid ' + AMBER + '">'
      '<h3 style="font-size:19.8px">Clients</h3>'
      '<p style="font-size:15.5px"><b class="hl">Flutter app</b> &mdash; the traveller '
      'journey end to end.</p>'
      '<p style="font-size:15.5px"><b class="hl">Next.js console</b> &mdash; catalog counts, '
      'the model registry, forecasts, festivals and the moderation queue.</p></div>'
      '<div class="card tint"><p style="font-size:15.5px"><b class="hl">Auth.</b> REST calls '
      'carry a SimpleJWT bearer token. The socket handshake verifies the same HS256 token '
      'with a shared secret.</p></div></div>'
    + '<div class="arrow">&#8594;</div>'
    + '<div class="col" style="width:330px">'
      '<div class="card solid" style="border-top:5px solid #6B911C">'
      '<h3 style="font-size:19.8px">core-engine &middot; Django</h3>'
      '<p style="font-size:15.5px">Owns the catalog and every write. Twelve applications: '
      'authentication, catalog, bookings, payments, permits, reviews, trust, '
      'recommendations, chat, workspace, currency, safety.</p>'
      '<p style="font-size:15.5px">Mounted at <code>/api/v1/</code> with URL path '
      'versioning, which is the source of one of the more instructive defects in Chapter 6.</p>'
      '</div>'
      '<div class="card dark"><p style="font-size:15.5px">Commits to PostgreSQL in a '
      'transaction, then publishes a compact event to Redis. The socket server subscribes '
      'and fans it out to the right rooms.</p></div></div>'
    + '<div class="arrow">&#8594;</div>'
    + '<div class="col" style="flex:1">'
      '<div class="card solid" style="border-top:5px solid ' + TEAL + '">'
      '<h3 style="font-size:19.8px">analytics-engine &middot; FastAPI</h3>'
      '<p style="font-size:15.5px">Internal only, authenticated with a shared service key. '
      'Never touches the database, so it stays independently testable.</p>'
      '<table class="t" style="margin-top:10px"><tr><th>Endpoint</th><th>Model</th></tr>'
      '<tr><td><code>/recommendations/routes</code></td><td>Logistic regression ranker</td></tr>'
      '<tr><td><code>/scam/score</code></td><td>Gradient boosting classifier</td></tr>'
      '<tr><td><code>/pricing/check</code></td><td>Benchmark rule + fair-wage flag</td></tr>'
      '<tr><td><code>/guides/rank</code></td><td>Ridge regression</td></tr>'
      '<tr><td><code>/forecasting/arrivals</code></td><td>Log-linear OLS</td></tr>'
      '<tr><td><code>/segments/assign</code></td><td>K-means, k = 4</td></tr></table></div></div>'
    + '</div>'
    + '<div class="card solid" style="border-left:6px solid ' + CRIMSON + '">'
      '<h3>Every machine-learning path has something behind it</h3>'
      '<div class="grid3" style="margin-top:10px">'
      '<div><b class="hl">Recommendations</b><p style="font-size:15.5px">If the ML service '
      'cannot be reached, routes come back ordered by badge points and guides by rating. The '
      'response carries a <code>source</code> field so the caller can tell which path ran.</p></div>'
      '<div><b class="hl">Price check</b><p style="font-size:15.5px">Falls back to a '
      'deterministic rule straight off the benchmark table, including the fair-wage floor, '
      'which is why that protection survives an outage.</p></div>'
      '<div><b class="hl">The catch</b><p style="font-size:15.5px">A fallback that works '
      'perfectly makes a broken integration invisible. The admin header now shows live '
      'service reachability for exactly this reason.</p></div>'
      '</div></div>'
    + '</div>'
    + foot("Service architecture and model placement"))



add("fig19_dataset", head(
    "Chapter 5 · The dataset",
    "500,000 Rows, Ten Linked Tables, and All Ten Now Feed a Model",
    "Generated with a fixed seed so the whole thing regenerates identically. "
    "Before this project's machine-learning phase, three of these tables were "
    "not referenced by any code at all.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill"><h3>Table sizes and what each one is for</h3>'
      '<div class="bars" style="margin-top:14px">'
    + bar("recommendation_interactions", 100, "140,000", TEAL, "ranking signal")
    + bar("bookings", 68, "95,000", TEAL, "transaction history")
    + bar("pricing_benchmarks", 61, "85,000", AMBER, "fair-price ground truth")
    + bar("tourist_arrivals", 43, "60,000", INDIGO, "forecasting series")
    + bar("tourists", 29, "40,000", TEAL, "survey profiles")
    + bar("scam_reports", 25, "35,000", CRIMSON, "labelled overcharges")
    + bar("gamification_log", 22, "31,000", AMBER, "badges and points")
    + bar("verified_guides", 6, "8,000", INDIGO, "NTB / IFMGA registry")
    + bar("cultural_events", 3, "4,000", AMBER, "festival calendar")
    + bar("trekking_routes", 1.5, "2,000", TEAL, "route catalog")
    + '</div></div>'
    + '<div class="col" style="width:420px">'
      '<div class="stat t"><b>500,000</b><span>rows across ten linked tables, one fixed seed</span></div>'
      '<div class="stat a"><b>10 / 10</b><span>tables now used by a model or by the profiling '
      'that shaped one &mdash; it was 7 of 10 before</span></div>'
      '<div class="card tint"><h3 style="font-size:18.6px">Why it is synthetic, and what that costs</h3>'
      '<p style="font-size:15.5px">A platform that has not launched has no interaction '
      'history to learn from, which is the cold start problem in all three of its forms. '
      'Generating the data also avoids processing real guides\' identities and livelihoods '
      'without asking them.</p>'
      '<p style="font-size:15.5px">The price is external validity, and it is stated here, in '
      'the findings and again in the threats to validity rather than tucked away once.</p></div>'
      '</div></div>'
    + '<div class="card solid"><h3>The three groups the tables fall into</h3>'
      '<div class="grid3" style="margin-top:11px">'
      '<div><span class="pill" style="background:#E1F1F2;color:#00838F">Reference</span>'
      '<p style="font-size:15.5px;margin-top:8px">The catalog. 2,000 routes with permits, '
      'difficulty, altitude, duration and seasonal closures. 8,000 guides with certification '
      'tier and licence number. 4,000 cultural events. 85,000 fair-price rows keyed by '
      'service, region and season.</p></div>'
      '<div><span class="pill mid">Behavioural</span>'
      '<p style="font-size:15.5px;margin-top:8px">What people did. 95,000 bookings, 140,000 '
      'interaction events covering views, wishlists, bookings, ratings, shares and '
      'completions, and 31,000 gamification records.</p></div>'
      '<div><span class="pill no">Analytical</span>'
      '<p style="font-size:15.5px;margin-top:8px">Support for specific models. 40,000 tourist '
      'profiles with survey-style preference scores, 60,000 arrival cohort records, and '
      '35,000 labelled scam reports.</p></div>'
      '</div></div>'
    + '</div>'
    + foot("Composition of the Travel Planning dataset"))


add("fig20_demand", head(
    "Chapter 5 · The demand picture",
    "Who Actually Travels, and When",
    "Profiled straight from the arrivals, tourists and bookings tables. This is "
    "the shape the forecaster and the segmentation model had to work with.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill"><h3>Arrivals by origin, 2021&ndash;2024 total</h3>'
      '<div class="bars" style="margin-top:13px">'
    + bar("South Asia", 100, "1.13m", TEAL)
    + bar("Europe", 65, "729k", INDIGO)
    + bar("East Asia", 59, "661k", TEAL)
    + bar("North America", 25, "284k", INDIGO)
    + bar("Oceania", 12, "137k", AMBER)
    + bar("Middle East", 5, "57k", AMBER)
    + bar("Latin America", 4, "43k", CRIMSON)
    + '</div>'
      '<p style="font-size:15.5px;margin-top:12px">Europe, North America and Oceania are '
      'also the three groups the generator deliberately quotes higher prices to, which is '
      'why they dominate the fairness audit in Chapter 6.</p></div>'
    + '<div class="card fill"><h3>Why people come</h3>'
      '<div class="bars" style="margin-top:13px">'
    + bar("Trekking", 100, "1.04m", "#6B911C")
    + bar("Cultural tour", 61, "635k", "#6B911C")
    + bar("Leisure / sightseeing", 38, "396k", "#8FB24E")
    + bar("Pilgrimage", 29, "300k", "#8FB24E")
    + bar("Adventure sports", 23, "241k", AMBER)
    + bar("Wildlife safari", 12, "126k", AMBER)
    + bar("Business and other", 30, "300k", GREY)
    + '</div>'
      '<p style="font-size:15.5px;margin-top:12px">Trekking and cultural touring together '
      'account for well over half of all arrivals, which is the reason the catalog and both '
      'recommender models are built around routes and festivals rather than hotels.</p></div>'
    + '</div>'
    + '<div class="row">'
    + '<div class="card fill"><h3>Arrivals by month, 2024 &mdash; the monsoon dip is the whole problem</h3>'
      '<div class="cols" style="height:230px;margin-top:10px">'
    + ''.join(col(v, p, m, c) for v, p, m, c in [
        ("113k", 59, "Jan", "#8FB24E"), ("119k", 62, "Feb", "#8FB24E"),
        ("157k", 82, "Mar", "#6B911C"), ("154k", 81, "Apr", "#6B911C"),
        ("158k", 83, "May", "#6B911C"), ("45k", 24, "Jun", GREY),
        ("45k", 24, "Jul", GREY), ("47k", 25, "Aug", GREY),
        ("184k", 96, "Sep", "#90C226"), ("179k", 94, "Oct", "#90C226"),
        ("191k", 100, "Nov", "#90C226"), ("120k", 63, "Dec", "#8FB24E")])
    + '</div><div class="axis"></div>'
      '<p style="font-size:15.5px;margin-top:11px">Autumn peaks at roughly four times the '
      'monsoon trough. Seasonality that swings this hard is exactly why the forecaster works '
      'on the logarithm of arrivals, so a month is a percentage of the year\'s level rather '
      'than a fixed number of visitors.</p></div>'
    + '<div class="col" style="width:400px">'
      '<div class="row" style="gap:12px">'
      '<div class="stat" style="flex:1"><b>39%</b><span>of travellers are<br>Budget band</span></div>'
      '<div class="stat t" style="flex:1"><b>28%</b><span>travel<br>Solo</span></div></div>'
      '<div class="row" style="gap:12px">'
      '<div class="stat a" style="flex:1"><b>59%</b><span>are aged<br>26 to 45</span></div>'
      '<div class="stat v" style="flex:1"><b>65%</b><span>book from the<br>mobile app</span></div></div>'
      '<div class="card tint"><p style="font-size:15.5px"><b class="hl">Concentration.</b> '
      'Pokhara and Annapurna alone take 34,449 of 95,000 bookings, more than a third. Everest '
      'and Khumbu take 13,651. The remaining thirteen regions share what is left, which is '
      'the same long-tail popularity bias Abdollahpouri et al. (2019) describe formally.</p></div>'
      '</div></div>'
    + '</div>'
    + foot("The demand side of the dataset"))


add("fig21_profiling", head(
    "Chapter 5 · Profiling before modelling",
    "One Real Signal, and Five That Do Not Exist",
    "The dataset documentation advertises several relationships between tourist "
    "attributes and behaviour. Checking them first, instead of assuming them, "
    "changed the whole design.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill solid" style="border-top:5px solid #6B911C">'
      '<span class="pill ok">Real, strong and monotonic</span>'
      '<h3 style="margin-top:11px">Adventure preference &rarr; booked route difficulty</h3>'
      '<div class="cols" style="height:220px;margin-top:12px">'
    + ''.join(col(v, p, m, "#6B911C") for v, p, m in [
        ("1.81", 56, "Q1<br>lowest"), ("2.16", 66, "Q2"), ("2.53", 78, "Q3"),
        ("2.88", 89, "Q4"), ("3.25", 100, "Q5<br>highest")])
    + '</div><div class="axis"></div>'
      '<p style="font-size:15.5px;margin-top:11px">11,900 positive route interactions split '
      'into quintiles by the tourist\'s adventure score. Mean booked difficulty rises '
      'cleanly from 1.81 to 3.25. Cost and altitude follow along, but only because both '
      'correlate with difficulty rather than carrying anything of their own.</p></div>'
    + '<div class="card fill solid" style="border-top:5px solid ' + CRIMSON + '">'
      '<span class="pill no">Flat &mdash; no signal at all</span>'
      '<h3 style="margin-top:11px">Five relationships the documentation claims</h3>'
      '<table class="t" style="margin-top:10px"><tr><th>Claimed signal</th><th>What the data shows</th></tr>'
      '<tr><td>Budget band &rarr; route cost</td><td class="n">$2,112 / 2,109 / 2,107 / 2,094</td></tr>'
      '<tr><td>Culture score &rarr; region</td><td class="n">shares differ &lt; 2 points</td></tr>'
      '<tr><td>Nature score &rarr; altitude</td><td class="n">4,510 / 4,507 / 4,508 / 4,525 / 4,498 m</td></tr>'
      '<tr><td>Fitness level &rarr; difficulty</td><td class="n">2.535 / 2.528 / 2.524 / 2.522</td></tr>'
      '<tr><td>Experience &rarr; difficulty</td><td class="n">2.546 / 2.524 / 2.527 / 2.515</td></tr></table>'
      '<p style="font-size:15.5px;margin-top:11px">Flat to within noise in every case. A '
      'model can only find what the generator put there, and five of the six things the '
      'documentation promised were simply not in the file.</p></div>'
    + '</div>'
    + '<div class="card dark"><h3>Why this mattered more than any algorithm choice</h3>'
      '<div class="row" style="gap:24px;margin-top:8px">'
      '<div style="flex:1"><p>The recommender that existed before this analysis was a '
      'hand-weighted score: <b style="color:#fff">45% adventure fit, 20% season fit, 20% '
      'budget fit, 15% popularity</b>. Two of those four terms, forty per cent of the whole '
      'score, were computed from relationships that do not exist.</p></div>'
      '<div style="flex:1"><p>The model was spending nearly half of every decision on noise, '
      'and no amount of tuning could have fixed it, because there was nothing there to tune '
      'toward. A human had already decided those features mattered, so a human was never '
      'going to find the problem.</p></div>'
      '</div></div>'
    + '</div>'
    + foot("What the profiling found before any model was built"))


add("fig22_limits", head(
    "Chapter 5 · Structural limits",
    "The Catalog Is Cloned Twice Over, and That Caps Every Metric",
    "This is a property of the data generator rather than of any model, and it "
    "is the single most important caveat in the whole evaluation.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill"><h3>Three levels, and only one of them is real</h3>'
      '<div style="display:flex;align-items:center;gap:16px;margin-top:16px">'
      f'<div style="flex:1;background:{TEAL};color:#fff;border-radius:12px;padding:20px;text-align:center">'
      '<b style="font-size:44.6px">2,000</b><br><span style="font-size:16.1px">route rows<br>'
      '<span style="opacity:.8">what a recommender ranks</span></span></div>'
      '<div class="arrow">&#8594;</div>'
      f'<div style="flex:1;background:{AMBER};color:#fff;border-radius:12px;padding:20px;text-align:center">'
      '<b style="font-size:44.6px">375</b><br><span style="font-size:16.1px">distinct names<br>'
      '<span style="opacity:.8">the concept granularity</span></span></div>'
      '<div class="arrow">&#8594;</div>'
      f'<div style="flex:1;background:{CRIMSON};color:#fff;border-radius:12px;padding:20px;text-align:center">'
      '<b style="font-size:44.6px">26</b><br><span style="font-size:16.1px">real treks<br>'
      '<span style="opacity:.8">what actually exists</span></span></div>'
      '</div>'
      '<p style="font-size:16.1px;margin-top:16px">Each real trek appears as roughly fifteen '
      'named variants &mdash; Everest Base Camp (Classic), (Budget), (Express) and so on &mdash; '
      'and each of those is duplicated five or six times over. So a recommender can identify '
      'exactly the right trek and still miss the specific route identifier that was booked.</p></div>'
    + '<div class="col" style="width:430px">'
      '<div class="card solid" style="border-top:5px solid ' + CRIMSON + '">'
      '<h3 style="font-size:19.8px">The ceiling this puts on precision</h3>'
      '<p style="font-size:15.5px">With 2,000 items, an average of 1.15 positive events per '
      'user, and the right answer hidden among fifteen near-identical twins, an absolute '
      'hit-rate at ten of around 1.4% is close to what this data permits.</p>'
      '<p style="font-size:15.5px">That is why the defensible claim in this thesis is a '
      'relative one against a baseline scored on the same protocol, and why it is never '
      'inflated into anything larger.</p></div>'
      '<div class="card tint"><h3 style="font-size:19.8px">The response: report at two granularities</h3>'
      '<p style="font-size:15.5px">Every ranking metric appears at <b class="hl">route '
      'level</b> and at <b class="hl">concept level</b>, so a reader can separate model '
      'performance from data artefact. And the served endpoint de-duplicates on the base '
      'trek, because four packagings of the same trail is not a shortlist.</p></div>'
      '</div></div>'
    + '<div class="card solid"><h3>Where else the data pushed back</h3>'
      '<div class="grid3" style="margin-top:11px">'
      '<div><b class="hl">Missing values, left alone</b><p style="font-size:15.5px">Five per '
      'cent of fitness levels and four per cent of preferred activities are missing. Neither '
      'is imputed with a guess. Fitness is not used by any model because profiling showed it '
      'carries nothing; activities are free text that the sparsity analysis said would not '
      'pay for itself.</p></div>'
      '<div><b class="hl">Ratings bunched in the middle</b><p style="font-size:15.5px">Of '
      '14,234 explicit ratings, 12,000 are threes and fours. Only 40 are a one. A '
      'distribution that narrow carries much less information than a five-point scale '
      'suggests, which shows up directly in the guide-matching result.</p></div>'
      '<div><b class="hl">A short forecasting series</b><p style="font-size:15.5px">Forty '
      'eight monthly observations, twelve of which are a post-pandemic anomaly running at a '
      'fifteenth of the 2024 level. Three years of a recovering series gives only two '
      'year-on-year growth observations to choose a method with.</p></div>'
      '</div></div>'
    + '</div>'
    + foot("The structural limits built into the data"))


add("fig23_features", head(
    "Chapter 5 · Feature engineering",
    "Thirteen Features Offered, One the Model Actually Wanted",
    "Standardised coefficients from the fitted logistic ranker. Given every "
    "feature and no instruction about which mattered, it found the answer on "
    "its own.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill"><h3>What the model learned, in its own weights</h3>'
      '<div class="bars" style="margin-top:14px">'
    + bar("gap_adventure", 100, "&minus;1.5924", CRIMSON, "the whole model")
    + bar("popularity", 9, "+0.1485", TEAL)
    + bar("pref_adventure_score", 5, "&minus;0.0840", GREY)
    + bar("duration_norm", 3.4, "+0.0536", GREY)
    + bar("gap_cost", 2, "+0.0307", GREY)
    + bar("altitude_norm", 1.9, "&minus;0.0296", GREY)
    + bar("gap_altitude", 1.7, "&minus;0.0276", GREY)
    + bar("remaining 6 features", 1, "all &lt; 0.013", GREY)
    + '</div>'
      '<p style="font-size:16.1px;margin-top:14px">The gap between a route\'s difficulty and '
      'the tourist\'s adventure score carries a coefficient more than ten times larger than '
      'anything else. Eight of the thirteen features sit below 0.03. The model concentrated '
      'almost everything on the one relationship the profiling had shown to be real, and '
      'drove the rest to approximately zero.</p></div>'
    + '<div class="col" style="width:440px">'
      '<div class="card solid" style="border-top:5px solid ' + TEAL + '">'
      '<h3 style="font-size:19.8px">The feature vector, thirteen elements</h3>'
      '<p style="font-size:15.5px"><b class="hl">5 survey scores</b> &mdash; culture, '
      'adventure, nature, risk tolerance, price sensitivity.</p>'
      '<p style="font-size:15.5px"><b class="hl">4 route attributes</b> &mdash; difficulty, '
      'cost, altitude and duration, each normalised to 0&ndash;1 so the coefficients can '
      'actually be read side by side.</p>'
      '<p style="font-size:15.5px"><b class="hl">3 cross terms</b> &mdash; the absolute gap '
      'between what the tourist wants and what the route offers, on adventure, altitude and '
      'cost.</p>'
      '<p style="font-size:15.5px"><b class="hl">1 popularity prior</b> &mdash; computed from '
      'the training period only, so nothing from the test year leaks back in.</p></div>'
      '<div class="card dark"><h3 style="font-size:19.8px">Why gaps and not raw pairs</h3>'
      '<p style="font-size:15.5px">Handing the model a tourist score and a route attribute '
      'separately and expecting it to learn the interaction between them needs a non-linear '
      'model. Handing it the gap directly lets a linear model capture the same relationship, '
      'which is how the explainability commitment survived without costing accuracy.</p></div>'
      '</div></div>'
    + '<div class="card tint"><h3>Two preparation decisions that mattered more than the algorithm</h3>'
      '<div class="grid2" style="margin-top:10px">'
      '<div><b class="hl">Negative sampling at 8 to 1.</b><p style="font-size:15.5px">Each '
      'observed positive is paired with eight routes drawn at random and labelled negative, '
      'which keeps the positive class near eleven per cent &mdash; high enough to train on '
      'without class weighting, low enough to still look like a ranking problem. Treating '
      'every unobserved pair as negative would be wrong anyway: a route the tourist never '
      'saw is not a route they rejected.</p></div>'
      '<div><b class="hl">What is deliberately not computed.</b><p style="font-size:15.5px">'
      'For the scam model, season is derived from the report month rather than joined from '
      'the benchmark table, because deriving it uses only what the app knows at request time '
      'whereas joining it would quietly import the benchmark the model is not allowed to '
      'see. Small distinction, and the difference between an honest score and a meaningless '
      'one.</p></div>'
      '</div></div>'
    + '</div>'
    + foot("Feature engineering and the coefficients the model learned"))



add("fig24_recommender", head(
    "Chapter 5 · Model 1",
    "The Route Recommender, and the Price of a Readable Shortlist",
    "A learned pointwise ranker rather than a hand-weighted score. The "
    "diversity cap that makes the list usable was measured, not guessed.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill"><h3>Ranking quality on the 2024 test year, 2,898 users</h3>'
      '<div class="bars" style="margin-top:14px">'
    + bar("Random ordering", 50, "0.0069", GREY)
    + bar("Popularity baseline", 60, "0.0083", SLATE, "the bar to clear")
    + bar("Old hand-weighted score", 65, "0.0090", AMBER, "1.08&times;, within noise")
    + bar("Learned ranker, capped", 83, "0.0114", "#6B911C", "1.38&times; &mdash; deployed")
    + bar("Learned ranker, raw", 98, "0.0135", TEAL, "1.63&times;")
    + '</div>'
      '<p style="font-size:15.5px;margin-top:13px">Hit-rate at ten. At concept level the '
      'same comparison runs 0.0462 for popularity against 0.0721 for the learned ranker, a '
      'lift of 1.56 times. NDCG at ten improves from 0.0039 to 0.0061.</p>'
      '<div class="vsep"></div>'
      '<p style="font-size:15.5px"><b class="hl">The number worth sitting with.</b> The '
      'hand-weighted heuristic managed 1.08 times over popularity, which is within noise of '
      'the baseline it was written to beat &mdash; and it looked completely reasonable as a '
      'piece of code. Without a comparator on the same protocol there would have been no way '
      'to know it was not working.</p></div>'
    + '<div class="col" style="width:470px">'
      '<div class="card solid" style="border-top:5px solid ' + AMBER + '">'
      '<h3 style="font-size:19.8px">The diversity cap, and what each setting costs</h3>'
      '<table class="t" style="margin-top:9px"><tr><th>Variants per trek</th><th>HR@10</th>'
      '<th>Concept HR@10</th><th>Lift</th></tr>'
      '<tr><td>Unconstrained</td><td class="n">0.0138</td><td class="n">0.0745</td><td class="n">1.67&times;</td></tr>'
      '<tr class="hi"><td>Max 3 &mdash; deployed</td><td class="n">0.0114</td><td class="n">0.0666</td><td class="n">1.38&times;</td></tr>'
      '<tr><td>Max 2</td><td class="n">0.0104</td><td class="n">0.0625</td><td class="n">1.25&times;</td></tr>'
      '<tr><td>Max 1</td><td class="n">0.0086</td><td class="n">0.0562</td><td class="n">1.04&times;</td></tr></table>'
      '<p style="font-size:15.5px;margin-top:10px">Collapsing to one row per trek destroys '
      'the advantage completely, because it removes the model\'s ability to choose which '
      'packaging suits the traveller. A cap of three guarantees at least four distinct treks '
      'in a top ten while keeping most of the gain.</p></div>'
      '<div class="card tint"><p style="font-size:15.5px"><b class="hl">Both numbers are '
      'reported throughout.</b> 1.63 times is how good the ranker is. 1.38 times is what the '
      'shipped endpoint achieves after a product decision about list quality. They answer '
      'different questions and collapsing them into one would be dishonest either way round.</p></div>'
      '</div></div>'
    + '<div class="card dark"><h3>Why it stayed a linear model</h3>'
      '<div class="row" style="gap:24px;margin-top:6px"><div style="flex:1">'
      '<p>Gradient boosting was tried and reached 0.0131 against logistic regression\'s '
      '0.0135, so the interpretable model was kept without any trade-off being needed. It is '
      'worth being honest that this means the explainability commitment was never really '
      'tested &mdash; had the boosted model been clearly better the decision would have been '
      'harder.</p></div><div style="flex:1">'
      '<p>What the linear model buys is that the reason shown on a card is computed from the '
      'same arithmetic that produced the ranking: each standardised feature value multiplied '
      'by its coefficient, largest positive contributors reported. It is not a separate '
      'story written next to the result.</p></div></div></div>'
    + '</div>'
    + foot("The route recommender and the accuracy-diversity trade-off"))


add("fig25_scam", head(
    "Chapter 5 · Model 2",
    "The Anti-Scam Classifier, and the Features Kept Out on Purpose",
    "The strongest model in the project, and the one closest to something "
    "deployable. Two whole categories of feature were excluded before any "
    "measurement was taken.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill solid" style="border-top:5px solid #6B911C">'
      '<span class="pill ok">Given to the model</span>'
      '<h3 style="margin-top:11px">Only what the app knows at request time</h3>'
      '<p style="font-size:16.1px">Service type, region, season and the quoted price, plus the '
      'log of the price because service prices span several orders of magnitude &mdash; a few '
      'hundred rupees for a trail meal against tens of thousands for a domestic flight.</p>'
      '<p style="font-size:16.1px">Season is derived from the report date rather than looked '
      'up, which is legitimate because the same derivation is available when a tourist types '
      'a price into their phone.</p></div>'
    + '<div class="card fill solid" style="border-top:5px solid ' + CRIMSON + '">'
      '<span class="pill no">Excluded on principle</span>'
      '<h3 style="margin-top:11px">Leakage, and protected attributes</h3>'
      '<p style="font-size:16.1px"><b class="hl">The overcharge ratio and the benchmark.</b> In '
      'the generator the label is a deterministic step on the ratio &mdash; the flag rate is '
      'exactly 0.000 in every bucket below 1.25 and exactly 1.000 above 1.30. Feeding either '
      'back would give a meaningless near-perfect score that reflects arithmetic, not learning.</p>'
      '<p style="font-size:16.1px"><b class="hl">Nationality and continent.</b> The dataset '
      'deliberately simulates real tourist-price discrimination. A model allowed to see '
      'nationality would learn to price-profile people, which is exactly the harm the '
      'platform exists to reduce. They appear only in the post-hoc audit.</p></div>'
    + '</div>'
    + '<div class="row">'
    + '<div class="card fill"><h3>Model selection turned on calibration, not accuracy</h3>'
      '<table class="t" style="margin-top:9px"><tr><th>Model</th><th>Accuracy</th><th>F1</th>'
      '<th>ROC-AUC</th><th>Brier</th></tr>'
      '<tr><td>Majority-class baseline</td><td class="n">0.786</td><td class="n">0.000</td>'
      '<td class="n">0.500</td><td class="n">0.214</td></tr>'
      '<tr><td>Logistic regression</td><td class="n">0.986</td><td class="n">0.966</td>'
      '<td class="n">0.999</td><td class="n">0.049</td></tr>'
      '<tr class="hi"><td>Gradient boosting &mdash; deployed</td><td class="n">0.991</td>'
      '<td class="n">0.980</td><td class="n">0.998</td><td class="n">0.006</td></tr></table>'
      '<p style="font-size:15.5px;margin-top:11px">ROC-AUC is effectively tied, so accuracy '
      'alone would not have justified the more complex model. The Brier score differs by '
      'roughly eight times. Because the application shows a <em>probability</em> to a user, '
      'how well that number is calibrated matters as much as how well the cases are ranked, '
      'and selecting on AUC alone would have shipped the worse-calibrated model.</p></div>'
    + '<div class="col" style="width:430px">'
      '<div class="card solid" style="border-top:5px solid ' + TEAL + '">'
      '<h3 style="font-size:19.8px">The harder test: cold cells</h3>'
      '<p style="font-size:15.5px">Sixty entire service-and-region combinations were held '
      'out, so the model is asked to judge quotes from cells it has never encountered. That '
      'is the realistic deployment case, because a tourist can type in any combination they '
      'like.</p>'
      '<div class="row" style="gap:11px;margin-top:12px">'
      '<div class="stat t" style="flex:1"><b>0.9989</b><span>ROC-AUC on<br>unseen cells</span></div>'
      '<div class="stat" style="flex:1"><b>0.958</b><span>F1 on<br>unseen cells</span></div></div>'
      '<p style="font-size:15.5px;margin-top:11px">Performance holds, which means the model '
      'learned the shape of the price relationship rather than memorising a lookup table.</p></div>'
      '<div class="card tint"><p style="font-size:15.5px"><b class="hl">And the honest '
      'caveat.</b> The task is easier than it looks. Because the label is a step function of '
      'a ratio, a model with service, region, season and price can reconstruct most of the '
      'decision boundary. The high score says the pipeline works, not that scam detection is '
      'solved.</p></div></div>'
    + '</div></div>'
    + foot("The anti-scam classifier"))


add("fig26_guides", head(
    "Chapter 5 · Model 3",
    "Guide Matching, and the Comparison Most Projects Never Run",
    "The improvement over the mean is modest. The finding underneath it is not.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill"><h3>Predicting the rating a specific traveller gives a specific guide</h3>'
      '<div class="bars" style="margin-top:14px">'
    + bar("Guide's own star rating", 100, "0.705", CRIMSON, "worse than the mean")
    + bar("Gradient boosting", 98, "0.692", GREY, "overfits 3,271 rows")
    + bar("Predict the global mean", 98, "0.688", SLATE, "the baseline")
    + bar("Ridge regression &mdash; deployed", 93, "0.655", "#6B911C", "4.8% better")
    + '</div>'
      '<p style="font-size:15.5px;margin-top:12px">RMSE on the 984 rated pairs in the 2024 '
      'test year, lower is better. Ridge also reaches MAE 0.511 and R&sup2; 0.093 against '
      '0.516 and 0.000 for the mean.</p></div>'
    + '<div class="card fill dark"><h3>The second row is the actual result</h3>'
      '<p>Ranking guides by their own registry-wide average rating &mdash; the obvious '
      'no-model strategy, and the one most platforms use &mdash; scores <b style="color:#fff">'
      'worse than predicting the average for everybody</b>.</p>'
      '<p>A guide\'s aggregate rating is a poor predictor of how one particular traveller '
      'will rate them. That converges with Zervas et al. (2021), who found Airbnb ratings '
      'compressed at the top of the scale, and with Ert et al. (2016), who found review '
      'scores carrying no effect on choice at all. Three different methods on three different '
      'datasets, all pointing the same way.</p>'
      '<p>It is the empirical argument for matching rather than sorting by stars, and it is '
      'exactly the kind of comparison that goes unrun in projects that only report their own '
      'model\'s score.</p></div>'
    + '</div>'
    + '<div class="row">'
    + '<div class="card fill solid" style="border-top:5px solid ' + TEAL + '">'
      '<h3 style="font-size:19.8px">What goes into it</h3>'
      '<p style="font-size:15.5px">4,255 explicit ratings from the interaction log, joined to '
      'both the guide registry and the tourist profile. Features cover certification tier, '
      'verification status, years of experience, registry rating, trips completed, and the '
      'breadth of languages and regions covered, alongside the requesting tourist\'s own '
      'survey scores.</p></div>'
    + '<div class="card fill solid" style="border-top:5px solid ' + AMBER + '">'
      '<h3 style="font-size:19.8px">Two rules deliberately outside the model</h3>'
      '<p style="font-size:15.5px"><b class="hl">Region and language are hard requirements</b>, '
      'not preferences. A guide who does not work in the requested region is not a candidate '
      'at all, and the data gives the model no way to learn that.</p>'
      '<p style="font-size:15.5px"><b class="hl">Verification is enforced after scoring</b>, so '
      'an expired licence is always demoted below a current one regardless of predicted match '
      'quality. A platform whose premise is verification cannot let a model score override it.</p></div>'
    + '<div class="card fill solid" style="border-top:5px solid ' + CRIMSON + '">'
      '<h3 style="font-size:19.8px">And its limits</h3>'
      '<p style="font-size:15.5px">4,255 rated pairs is a small sample, and only 984 of them '
      'fall in the test year, so a 4.8% improvement is modest relative to that. Gradient '
      'boosting was tried and overfitted. The honest description is marginal on its own terms '
      'and useful mainly for what it says about star ratings.</p></div>'
    + '</div></div>'
    + foot("Guide matching against two baselines"))


add("fig27_forecast", head(
    "Chapter 5 · Model 4",
    "Arrivals Forecasting, and a Result That Flips Between Years",
    "Error roughly halved against the standard seasonal benchmark on the test "
    "year. On the validation year the ranking inverts completely, and that is "
    "reported rather than buried.")
    + '<div class="body">'
    + '<div class="card fill" style="margin-bottom:16px"><h3>2024 test year &mdash; actual against predicted, by month</h3>'
      '<div style="display:flex;gap:9px;height:210px;align-items:flex-end;margin-top:14px">'
    + ''.join(
        f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%">'
        f'<div style="display:flex;gap:3px;align-items:flex-end;width:100%;height:100%">'
        f'<div style="flex:1;height:{a}%;background:#6B911C;border-radius:4px 4px 0 0"></div>'
        f'<div style="flex:1;height:{p}%;background:{TEAL};border-radius:4px 4px 0 0;opacity:.62"></div>'
        f'</div><div class="cl">{m}</div></div>'
        for m, a, p in [
            ("Jan", 52, 63), ("Feb", 55, 61), ("Mar", 72, 88), ("Apr", 71, 87),
            ("May", 73, 88), ("Jun", 21, 24), ("Jul", 21, 24), ("Aug", 21, 24),
            ("Sep", 85, 99), ("Oct", 82, 97), ("Nov", 88, 100), ("Dec", 55, 64)])
    + '</div><div class="axis"></div>'
      '<div style="display:flex;gap:22px;margin-top:12px;font-size:15.5px;color:#4E594F">'
      '<span><span style="display:inline-block;width:13px;height:13px;background:#6B911C;'
      'border-radius:3px;vertical-align:-2px"></span> Actual arrivals</span>'
      f'<span><span style="display:inline-block;width:13px;height:13px;background:{TEAL};'
      'opacity:.62;border-radius:3px;vertical-align:-2px"></span> Model projection</span>'
      '<span style="color:#98A093">The shape is right everywhere; the level runs consistently '
      'a little high, which is what a trend fitted through a recovering series does.</span></div></div>'
    + '<div class="row">'
    + '<div class="card fill"><h3>Against every baseline, 2024</h3>'
      '<table class="t" style="margin-top:9px"><tr><th>Method</th><th>MAE</th><th>RMSE</th><th>MAPE</th></tr>'
      '<tr><td>Mean of last 12 months</td><td class="n">64,164</td><td class="n">70,976</td><td class="n">53.0%</td></tr>'
      '<tr><td>Seasonal naive</td><td class="n">48,006</td><td class="n">51,667</td><td class="n">38.6%</td></tr>'
      '<tr><td>Seasonal naive &times; growth</td><td class="n">23,666</td><td class="n">26,624</td><td class="n">17.8%</td></tr>'
      '<tr class="hi"><td>Log-linear trend + seasonality</td><td class="n">22,515</td><td class="n">25,076</td><td class="n">17.2%</td></tr></table>'
      '<p style="font-size:15.5px;margin-top:11px">OLS on the logarithm of arrivals against a '
      'time index and twelve month indicators, fitted on the trailing twenty four months. '
      'Taking logs makes the seasonality multiplicative, which is what a recovering series '
      'needs. Restricting to twenty four months was a domain call made before the test year '
      'was opened: 2021 runs at a fifteenth of 2024 and would distort any trend through it.</p></div>'
    + '<div class="col" style="width:450px">'
      '<div class="card solid" style="border-top:5px solid ' + CRIMSON + '">'
      '<h3 style="font-size:19.8px">The negative result, reported in full</h3>'
      '<p style="font-size:15.5px">On the <b class="hl">2023 validation year the ranking '
      'inverts</b>. Seasonal naive wins at 47.6% MAPE while this model reaches 155%, because '
      'fitting on 2021 to 2022 puts the 4.85 times post-COVID recovery spike inside the trend '
      'window.</p>'
      '<p style="font-size:15.5px">Three years of a recovery-distorted series gives two '
      'year-on-year growth observations, which is not enough to select a forecasting method '
      'with any confidence. The deployed model wins the genuine held-out year and is '
      'principled in construction, but the disagreement is real and it is surfaced in the '
      'model card, in the API response and in the admin interface.</p></div>'
      '<div class="card tint"><p style="font-size:15.5px"><b class="hl">A correctness bug '
      'worth recording.</b> The training script originally registered the <em>evaluation</em> '
      'model, fitted a year behind the artifact\'s own metadata, so serving extrapolated an '
      'extra year of compounding growth on every request &mdash; a 2026 forecast of 6.5 '
      'million against a real figure nearer 1.15 million. Evaluation and serving fits are now '
      'separate, and the 2025 projection went from 2.25 times the previous year to 1.64, '
      'against an observed 1.62.</p></div></div>'
    + '</div></div>'
    + foot("Arrivals forecast against baselines, and its reliability horizon"))


add("fig28_segments", head(
    "Chapter 5 · Model 5",
    "Segmentation: the Model That Did Not Work, Kept In Anyway",
    "A flat silhouette curve at every k is itself the finding. There is no "
    "natural cluster structure in this data at all.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill"><h3>Silhouette across every k tried</h3>'
      '<div class="cols" style="height:210px;margin-top:12px">'
    + ''.join(col(v, p, f"k = {k}", GREY if k != 4 else CRIMSON)
              for k, v, p in [(2, "0.138", 100), (3, "0.131", 95), (4, "0.133", 96),
                              (5, "0.133", 96), (6, "0.138", 100), (7, "0.136", 99),
                              (8, "0.137", 99)])
    + '</div><div class="axis"></div>'
      '<p style="font-size:15.5px;margin-top:12px">Perfectly flat at roughly 0.13 everywhere. '
      'The generator drew the five preference scores close to independently, so the preference '
      'space is one diffuse cloud rather than a set of groups. Choosing four is picking a '
      'convenient partition, not discovering personas.</p></div>'
    + '<div class="card fill"><h3>So it was validated on behaviour instead</h3>'
      '<p style="font-size:15.5px">Geometry alone would have condemned the model, so the '
      'question was changed: does segment membership predict what people actually book?</p>'
      '<table class="t" style="margin-top:11px"><tr><th>Segment</th><th>Size</th>'
      '<th>Bookings</th><th>Mean difficulty</th></tr>'
      '<tr><td>Budget-conscious / nature-loving</td><td class="n">10,276</td><td class="n">3,027</td><td class="n">2.587</td></tr>'
      '<tr><td>Risk-tolerant</td><td class="n">10,047</td><td class="n">2,949</td><td class="n">2.514</td></tr>'
      '<tr><td>Urban-leaning / budget-conscious</td><td class="n">9,503</td><td class="n">2,838</td><td class="n">2.544</td></tr>'
      '<tr><td>Comfort-spending / safety-first</td><td class="n">10,174</td><td class="n">3,086</td><td class="n">2.450</td></tr></table></div>'
    + '</div>'
    + '<div class="row">'
    + '<div class="card fill solid" style="border-top:5px solid ' + AMBER + '">'
      '<h3 style="font-size:19.8px">Statistically unambiguous</h3>'
      '<p style="font-size:16.1px">One-way ANOVA on the difficulty of routes members actually '
      'booked gives <b class="hl">F = 21.01</b> with <b class="hl">p &asymp; 1.4 &times; '
      '10&#8315;&sup1;&sup3;</b>. The segments genuinely do differ.</p></div>'
    + '<div class="card fill solid" style="border-top:5px solid ' + CRIMSON + '">'
      '<h3 style="font-size:19.8px">And practically minor</h3>'
      '<p style="font-size:16.1px">The spread between the extreme segments is 0.137 against a '
      'pooled standard deviation of 0.699 &mdash; <b class="hl">Cohen\'s d &asymp; 0.20</b>, a '
      'small effect. Reporting only the p-value would have made a fifth of a standard '
      'deviation sound like a discovery.</p></div>'
    + '<div class="card fill dark"><h3 style="font-size:19.8px">Why it stayed in the thesis</h3>'
      '<p style="font-size:16.1px">It would have been easy to drop it and present four '
      'successes. It is here because the pattern it exposes &mdash; a tiny p-value attached to '
      'a trivial effect &mdash; is one of the most common ways quantitative results get '
      'overstated. The segments are used as a cold-start default and are deliberately never '
      'shown to a user as their travel personality.</p></div>'
    + '</div></div>'
    + foot("Tourist segmentation, and why it is reported as weak"))


add("fig29_fairwage", head(
    "Chapter 5 · The fair-wage protection",
    "A Price Check That Looks in Both Directions",
    "Publishing a fair range helps a tourist spot an overcharge. It equally "
    "helps them anchor every negotiation at the floor of that range, and for a "
    "guide or a porter the floor is a day's wage.")
    + '<div class="body">'
    + '<div class="card solid" style="margin-bottom:16px">'
      '<h3>A worked example &mdash; licensed guide, Everest and Khumbu, autumn peak</h3>'
      '<p style="font-size:16.1px;margin-bottom:14px">Fair benchmark <b class="hl">4,740 NPR '
      'per day</b>, fair range <b class="hl">3,673 to 5,806</b>. Three quotes, three '
      'different outcomes.</p>'
      '<div class="grid3">'
      f'<div style="background:#FBE7E5;border:1px solid #F2C9C4;border-left:6px solid {CRIMSON};'
      'border-radius:12px;padding:17px">'
      f'<div style="font-size:37.2px;font-weight:700;color:{CRIMSON}">NPR 18,000</div>'
      '<span class="pill no" style="margin-top:9px">Likely scam</span>'
      '<p style="font-size:15.5px;margin-top:10px">3.80 times the benchmark. Flagged with a '
      'probability of 1.0 and the benchmark shown alongside, so the traveller can see what '
      'the number is being compared against.</p></div>'
      '<div style="background:#EDF7DA;border:1px solid #D5E7B4;border-left:6px solid #6B911C;'
      'border-radius:12px;padding:17px">'
      '<div style="font-size:37.2px;font-weight:700;color:#4A6316">NPR 4,700</div>'
      '<span class="pill ok" style="margin-top:9px">Fair</span>'
      '<p style="font-size:15.5px;margin-top:10px">Inside the range and essentially on the '
      'benchmark. Reported as fair, with no nudge to push it lower.</p></div>'
      f'<div style="background:#FCF0DC;border:1px solid #EFD9AF;border-left:6px solid {AMBER};'
      'border-radius:12px;padding:17px">'
      f'<div style="font-size:37.2px;font-weight:700;color:#A66400">NPR 2,000</div>'
      '<span class="pill mid" style="margin-top:9px">Below fair wage</span>'
      '<p style="font-size:15.5px;margin-top:10px">45.5% under the fair rate. Rendered as its '
      'own outcome with its own colour and icon, with the message that paying under the range '
      'pushes licensed workers out of the market.</p></div>'
      '</div></div>'
    + '<div class="row">'
    + '<div class="card fill"><h3>How the rule works</h3>'
      '<p style="font-size:16.1px">A quote below <b class="hl">95% of the fair floor</b> for a '
      '<b class="hl">labour</b> service &mdash; licensed guide or porter &mdash; raises the '
      'below-fair-wage flag. Permits, meals and transport are exempt, because a cheap permit '
      'is a fee rather than somebody\'s underpaid labour.</p>'
      '<p style="font-size:16.1px">It is enforced independently in the analytics engine and in '
      'the core engine\'s fallback path, with tests in both services, so the protection '
      'survives an outage of the machine-learning service. That redundancy is deliberate: a '
      'protection that disappears when a service goes down is not really a protection.</p></div>'
    + '<div class="card fill dark"><h3>What it does not do</h3>'
      '<p>The rule is a threshold on a benchmark, not a model. It protects against '
      'under-quoting <b style="color:#fff">on the platform</b>. It does nothing about a '
      'negotiation that happens off-platform, and nothing about an oversupply of guides '
      'pushing the benchmark itself downward over time.</p>'
      '<p>It addresses the mechanism the platform itself creates, which is the part the '
      'platform is responsible for, and no more than that. Fairness research on recommenders '
      'is overwhelmingly user-side, so a concrete supply-side protection is a small '
      'contribution in an under-populated area &mdash; but a small one.</p></div>'
    + '</div></div>'
    + foot("The two-sided price check and the fair-wage rule"))



add("fig30_product", head(
    "Chapter 5 · The delivered product",
    "What Was Actually Shipped, on Both Clients",
    "The models are only worth anything if somebody can reach them, so a large "
    "share of the effort went into the two client applications.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill solid" style="border-top:5px solid ' + AMBER + '">'
      '<h3>Flutter mobile application</h3>'
      '<p style="font-size:15.5px">Organised feature-first, each feature split into data, '
      'domain and presentation. The data layer returns a record of failure and value rather '
      'than throwing, so every caller has to handle the failure case out loud. The domain '
      'layer has no Flutter imports at all.</p>'
      '<div class="grid2" style="margin-top:13px;gap:9px">'
    + ''.join(
        f'<div style="background:#F4F8EC;border-radius:9px;padding:10px 12px">'
        f'<b style="font-size:16.1px;color:#3E5514">{t}</b>'
        f'<p style="font-size:14.6px;margin-top:3px;color:#5A655C">{d}</p></div>'
        for t, d in [
            ("Auth", "Email and password with silent token refresh in an interceptor, so an "
             "expired token never bounces you to the login screen."),
            ("Explore &amp; Guides", "The dataset-backed catalog, searchable, with guide "
             "profiles showing certification and licence."),
            ("Home recommendations", "A personalised strip where every card shows the top "
             "reason the ranker produced. This is where explainability becomes visible to a "
             "real user rather than staying an API field."),
            ("Price check", "Three distinct outcomes rendered differently: overpriced, fair, "
             "and below fair wage with its own colour so it is never mistaken for a bargain."),
            ("Bookings &amp; payments", "Package-centric booking with a simulated eSewa and "
             "Khalti sheet and confirmation."),
            ("Reviews", "Rate and review a guide, held in a pending state until a moderator "
             "acts on it."),
            ("Live chat", "Socket.IO with REST history, opened from a booking or the home "
             "screen."),
            ("Workspace", "Day-by-day itinerary with drag-and-drop reordering, a budget bar "
             "and AI itinerary suggestions."),
            ("Currency &amp; SOS", "A converter with a session-wide preference, and an "
             "emergency alert screen."),
            ("Festivals", "The cultural calendar grouped by month, from the events table."),
        ])
    + '</div></div>'
    + '<div class="card fill solid" style="border-top:5px solid ' + CRIMSON + '">'
      '<h3>Next.js admin console</h3>'
      '<p style="font-size:15.5px">Built with shadcn/ui on Base UI primitives. Five pages: an '
      'overview with catalog counts and model summaries, a model registry listing every '
      'trained model with its headline metric and full model card, a demand forecast page, a '
      'festival calendar, and a scam-report moderation queue.</p>'
      '<div class="vsep"></div>'
      '<p style="font-size:15.5px"><b class="hl">Every protected read is server-side.</b> They '
      'happen in React Server Components, so the machine-learning service key and the staff '
      'token never enter the browser bundle.</p>'
      '<p style="font-size:15.5px"><b class="hl">The header shows live service health.</b> This '
      'exists because of the failure mode in Chapter 6 &mdash; the platform degrades silently, '
      'so without an explicit indicator a working system and a broken one look identical from '
      'the outside.</p>'
      '<p style="font-size:15.5px"><b class="hl">The moderation queue is the one place it '
      'writes.</b> The core engine had exposed verify and dismiss on scam reports since the '
      'fourth sprint and nothing had ever called them. Wiring them through Server Actions '
      'keeps the token server-side, and each action is confirmed in a dialog first, because '
      'verifying a report changes a provider\'s standing and should not be one misplaced '
      'click. Failures surface loudly rather than silently.</p></div>'
    + '</div>'
    + '<div class="row">'
    + ''.join(
        f'<div class="stat {cl}" style="flex:1"><b>{v}</b><span>{d}</span></div>'
        for v, d, cl in [
            ("5", "deployable units<br>in one monorepo", ""),
            ("12", "Django applications<br>behind the API", "t"),
            ("58", "automated tests<br>across four services", "a"),
            ("36", "API operations exercised<br>in the scripted journey", "v"),
            ("96", "commits on main<br>across six branches", "r"),
        ])
    + '</div></div>'
    + foot("The delivered mobile application and admin console"))


# ==========================================================================
# CHAPTER 6 — FINDINGS AND DISCUSSION
# ==========================================================================
add("fig31_results", head(
    "Chapter 6 · RQ1 results",
    "Five Models, Five Baselines, One Test Year",
    "Every model shown next to a comparator scored through the same harness on "
    "the 2024 data it never saw in training.")
    + '<div class="body">'
    + '<div class="row" style="gap:13px;margin-bottom:16px">'
    + ''.join(
        f'<div class="card fill solid" style="border-top:5px solid {c}">'
        f'<h3 style="font-size:19.8px">{t}</h3>'
        f'<p style="font-size:14.6px;color:#8A938B;margin-bottom:12px">{metric}</p>'
        f'<div style="display:flex;align-items:flex-end;gap:14px;height:130px">'
        f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%">'
        f'<div class="cv">{bv}</div><div class="cbar" style="height:{bp}%;background:{GREY}"></div></div>'
        f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%">'
        f'<div class="cv">{mv}</div><div class="cbar" style="height:{mp}%;background:{c}"></div></div>'
        f'</div><div class="axis"></div>'
        f'<div style="display:flex;gap:14px;font-size:14.3px;color:#6D766C;margin-top:6px">'
        f'<span style="flex:1;text-align:center">{bl}</span>'
        f'<span style="flex:1;text-align:center">{ml}</span></div>'
        f'<div style="margin-top:11px;padding:9px;background:#F4F8EC;border-radius:8px;'
        f'text-align:center;font-size:15.5px;font-weight:600;color:{c}">{note}</div>'
        f'<p style="font-size:14.6px;margin-top:9px">{verdict}</p></div>'
        for t, metric, bv, bp, bl, mv, mp, ml, note, verdict, c in [
            ("Route recommendation", "Hit-rate@10 · higher is better",
             "0.0083", 61, "Popularity", "0.0135", 100, "Learned ranker",
             "1.63&times; the baseline",
             "<b class='hl'>Modest but real.</b> Small in absolute terms for reasons the data "
             "explains, and the relative claim is the defensible one.", TEAL),
            ("Anti-scam detection", "Accuracy · higher is better",
             "78.6%", 79, "Majority class", "99.1%", 100, "Gradient boosting",
             "F1 0.980 &middot; Brier 0.006",
             "<b class='hl'>Strong.</b> Holds at F1 0.958 on sixty service and region "
             "combinations it had never seen.", CRIMSON),
            ("Guide matching", "RMSE · lower is better",
             "0.688", 100, "Predict the mean", "0.655", 95, "Ridge regression",
             "4.8% better than the mean",
             "<b class='hl'>Marginal.</b> But sorting by a guide's own star rating scores "
             "0.705, worse than the mean.", INDIGO),
            ("Arrivals forecast", "MAPE · lower is better",
             "38.6%", 100, "Seasonal naive", "17.2%", 45, "Log-trend model",
             "Error roughly halved",
             "<b class='hl'>Moderate.</b> Model selection does not replicate across years, so "
             "it is indicative rather than settled.", AMBER),
            ("Segmentation", "Silhouette · higher is better",
             "&mdash;", 0, "No comparator", "0.13", 26, "K-means, k = 4",
             "Flat at every k tried",
             "<b class='hl'>Weak.</b> No natural structure. Behavioural effect is real but "
             "tiny, d &asymp; 0.20.", SLATE),
        ])
    + '</div>'
    + '<div class="card dark"><h3>The pattern across all five, which is the answer to RQ1</h3>'
      '<div class="row" style="gap:24px;margin-top:6px">'
      '<div style="flex:1"><p>The models succeed roughly <b style="color:#fff">in proportion '
      'to the density of signal available to them</b>. Scam risk, built on structured '
      'reference data with a clean label, is strong. Forecasting, built on an aggregate time '
      'series, is moderate. Recommendation and guide matching, which depend on behavioural '
      'history a pre-launch market has not generated, are modest. Segmentation, which depends '
      'on latent structure that simply is not there, is weak.</p></div>'
      '<div style="flex:1"><p>The practical implication is worth more than any individual '
      'number. For a platform of this kind in an informal market, <b style="color:#fff">build '
      'the price benchmark and the verified registry first</b>, and treat personalisation as '
      'something that improves after launch once real interaction data exists. That ordering '
      'is the opposite of how these products are usually pitched.</p></div>'
      '</div></div>'
    + '</div>'
    + foot("Model performance against baselines, test year 2024"))


add("fig32_fairness", head(
    "Chapter 6 · RQ2 results",
    "The Disparity Is in the Market, Not in the Classifier",
    "A per-continent audit of the anti-scam model. The flag-rate spread trips "
    "the project's own gate, and the interpretation matters more than the "
    "number does.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill"><h3>Model flag rate against the group\'s actual overcharge rate</h3>'
      '<table class="t" style="margin-top:10px"><tr><th>Continent</th><th>n</th>'
      '<th>Model flag rate</th><th>Actual rate</th><th>Difference</th><th>ROC-AUC</th></tr>'
    + ''.join(
        f'<tr{cls}><td>{g}</td><td class="n">{n}</td><td class="n">{f}</td>'
        f'<td class="n">{a}</td><td class="n" style="color:{dc}">{d}</td><td class="n">{auc}</td></tr>'
        for g, n, f, a, d, dc, auc, cls in [
            ("Europe", "1,939", "0.306", "0.302", "+0.004", "#8A5A00", "0.996", ' class="hi"'),
            ("North America", "826", "0.315", "0.320", "&minus;0.005", "#8A5A00", "0.997", ' class="hi"'),
            ("Oceania", "387", "0.305", "0.308", "&minus;0.003", "#8A5A00", "0.999", ' class="hi"'),
            ("Latin America", "139", "0.180", "0.180", "0.000", "#1F6B34", "1.000", ""),
            ("South Asia", "3,227", "0.162", "0.162", "0.000", "#1F6B34", "1.000", ""),
            ("East Asia", "1,874", "0.154", "0.154", "0.000", "#1F6B34", "1.000", ""),
            ("Middle East", "150", "0.153", "0.147", "+0.006", "#1F6B34", "0.998", ""),
        ])
    + '</table>'
      '<p style="font-size:15.5px;margin-top:12px">The three highlighted rows are the three '
      'groups the data generator deliberately quotes higher prices to, mirroring documented '
      'tourist-price discrimination. Their flag rate is roughly twice everybody else\'s, and '
      'so is the rate at which they are genuinely overcharged.</p></div>'
    + '<div class="col" style="width:430px">'
      '<div class="stat r"><b>0.1615</b><span>flag-rate disparity, against the project\'s own '
      '0.15 gate</span></div>'
      '<div class="stat"><b>&lt; 0.006</b><span>largest gap between a group\'s flag rate and '
      'its actual overcharge rate</span></div>'
      '<div class="card solid" style="border-top:5px solid ' + AMBER + '">'
      '<h3 style="font-size:19.8px">The gate worked</h3>'
      '<p style="font-size:15.5px">Exceeding 0.15 routes the model to <b class="hl">review '
      'rather than silent deployment</b>. That is the guardrail doing its job, not a failure. '
      'What it is not is a signal to go and tune the disparity away.</p></div></div>'
    + '</div>'
    + '<div class="row">'
    + '<div class="card fill dark"><h3>Why equalising the flag rates would be the wrong fix</h3>'
      '<p>A detector tuned to flag every group equally would systematically '
      '<b style="color:#fff">under-protect exactly the tourists being targeted most</b>. '
      'European, North American and Oceanian visitors genuinely are quoted higher prices in '
      'this data, and a model that pretended otherwise would be worse at the job it exists to '
      'do.</p>'
      '<p>This is a textbook instance of Chouldechova\'s (2017) impossibility result: when '
      'base rates differ between groups, calibration within groups and equal error rates '
      'across groups cannot both hold. Choosing between them is a normative decision, not a '
      'technical one.</p></div>'
    + '<div class="card fill tint"><h3>The position this project takes, stated as a position</h3>'
      '<p><b class="hl">Calibrate to the world.</b> Report what is actually happening rather '
      'than a smoothed version of it.</p>'
      '<p><b class="hl">Never take nationality as an input.</b> Not as a feature, not as a '
      'proxy. It appears only in the audit.</p>'
      '<p><b class="hl">Make the result inspectable rather than tuning it away.</b> Return the '
      'benchmark, the ratio and the reasoning with every score.</p>'
      '<p style="margin-top:10px">Whether that is the right choice is arguable, and a critic '
      'could fairly say that a platform flagging European quotes twice as often is producing '
      'a visible pattern providers will notice. The thesis presents this as a choice rather '
      'than a proof.</p></div>'
    + '</div></div>'
    + foot("Per-continent fairness audit of the anti-scam classifier"))


add("fig33_defects", head(
    "Chapter 6 · What running the system revealed",
    "Ten Defects a Green Test Suite Never Caught",
    "None of them was a logic bug. Every single one was wiring &mdash; a "
    "settings default, a URL keyword argument, a mismatched key, a room name.")
    + '<div class="body">'
    + '<table class="t"><tr><th style="width:300px">What broke</th><th>Root cause</th>'
      '<th style="width:290px">Why the tests stayed green</th><th style="width:170px">Now guarded by</th></tr>'
    + ''.join(
        f'<tr><td><b class="hl">{w}</b></td><td>{r}</td><td>{h}</td><td>{g}</td></tr>'
        for w, r, h, g in [
            ("Nothing was migrated, so the app could not serve at all",
             "The development database existed at zero bytes; no migration had ever been applied.",
             "pytest builds a fresh test database on every run, so 34 tests passed against a "
             "schema the real database did not have.",
             "Documented setup path from a fresh clone"),
            ("Every cached endpoint returned a 500",
             "The development settings documented themselves as needing no external services "
             "but inherited a Redis cache from the base settings.",
             "The test config swapped in a local-memory cache so the suite would be hermetic. "
             "That made the suite pass while the application stayed broken.",
             "Local-memory fallback unless REDIS_URL is set"),
            ("Fourteen API actions raised TypeError on every single call",
             "The API is mounted under a versioned URL prefix, so Django passes an extra "
             "keyword into every handler. Four handlers accepted it; fourteen did not.",
             "No test called any of the fourteen. The four that were tested happened to be "
             "the ones written correctly.",
             "A contract test that walks the URL conf"),
            ("The user's own profile endpoint returned 403 to that user",
             "A permission method fell through to admin-only for anything outside the CRUD "
             "actions, silently overriding the action's own declaration.",
             "Nothing exercised the self-service route as a normal authenticated user.",
             "Parametrised tests over the self-service routes"),
            ("Every machine-learning call was rejected, and nothing looked wrong",
             "The two services disagreed on the default API key, so the ML service answered "
             "401 to everything.",
             "The graceful-degradation path worked perfectly. The feed always returned "
             "results, so the outside view was identical to a healthy system.",
             "Matched defaults, plus a live health indicator"),
            ("The socket server never bound its port, so chat was completely dead",
             "The Redis client retried forever and the listen call came after the bridge, so "
             "the server never got as far as binding.",
             "The real-time engine had no tests at all before this point.",
             "Binds first; the Redis bridge is optional"),
            ("Every socket handshake was rejected",
             "The JWT secret defaults differed between Django and the Node service, and the "
             "token verifier required a numeric user id where SimpleJWT emits a string.",
             "Same reason &mdash; nothing tested the handshake.",
             "Tests pinning the authentication contract"),
            ("Chat messages went to an empty room",
             "Booking events fanned out on the booking reference while both the app and "
             "Django parse the booking primary key.",
             "Both sides were individually correct. Only the convention between them was wrong.",
             "Tests pinning the room naming convention"),
            ("The forecaster served a model fitted a year behind its own metadata",
             "The training script registered the evaluation fit, so serving extrapolated an "
             "extra year of compounding growth on every request.",
             "The metrics were honest and the artifact loaded cleanly. Nothing compared the "
             "two.",
             "Horizon assertions on the served model"),
            ("The dashboard compounded that error further",
             "It defaulted to the current calendar year rather than the first year past the "
             "data.",
             "A rendering default that no test asserted on.",
             "Defaults to the first year past the data"),
        ])
    + '</table>'
    + '<div class="row" style="margin-top:16px">'
    + '<div class="card fill dark"><h3>The lesson, and it generalises</h3>'
      '<p>A test suite that exercises functions in isolation will confirm that each function '
      'is correct while telling you nothing about whether the functions are connected to each '
      'other correctly. In a system with five services, two languages and several shared '
      'secrets, <b style="color:#fff">the connections are where the risk lives</b>.</p>'
      '<p>Two of these were invisible for a subtler reason still. The system degrades '
      'gracefully by design, so a broken integration returned a 200 and a plausible list. '
      'Graceful degradation is good engineering and it is also a very effective way to hide a '
      'broken integration.</p></div>'
    + '<div class="card fill tint"><h3>What was added in response</h3>'
      '<p>Not more unit tests. Tests shaped like these failures.</p>'
      '<p><b class="hl">A contract test</b> walks the URL configuration and inspects every '
      'mounted handler\'s signature, so a future handler with the wrong shape fails '
      'immediately and names itself.</p>'
      '<p><b class="hl">Client-patched integration tests</b> exercise the ML path and the '
      'fallback path separately, rather than depending on whether a service happens to be '
      'running.</p>'
      '<p><b class="hl">Horizon assertions</b> catch a model being served outside the range '
      'its own metrics describe.</p>'
      '<p>The suite went from 26 tests to <b class="hl">58</b>, concentrated on the '
      'connections rather than on more coverage of functions that already worked.</p></div>'
    + '</div></div>'
    + foot("Defects found by running the system, and the tests now guarding them"), h=1900)


add("fig34_verification", head(
    "Chapter 6 · End-to-end verification",
    "Every Claim in This Report Checked Against Running Software",
    "Because the thesis claims a working platform and not only a set of models, "
    "the whole stack was run and exercised rather than read.")
    + '<div class="body">'
    + '<div class="grid4" style="margin-bottom:16px">'
    + ''.join(
        f'<div class="stat {cl}"><b>{v}</b><span>{d}</span></div>'
        for v, d, cl in [
            ("4", "services started with no Docker, no Redis and no PostgreSQL &mdash; on "
             "SQLite and an in-process cache", ""),
            ("23s", "to retrain all five models from scratch, so any figure in this report "
             "regenerates with one command", "t"),
            ("36 / 36", "API operations in the scripted traveller journey passed, from "
             "registration through to a review summary", "a"),
            ("99,000+", "catalog rows seeded live: 2,000 routes, 8,000 guides, 4,000 events, "
             "85,000 benchmarks, 15 regions", "v"),
        ])
    + '</div>'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill"><h3>Three results that verify specific claims made earlier</h3>'
      '<div style="display:flex;gap:12px;margin-top:13px">'
      f'<div class="num" style="background:{TEAL}">1</div><div>'
      '<b class="hl">The ML service was really being used.</b>'
      '<p style="font-size:15.5px">The recommendation endpoints returned a source field of '
      '"ml" rather than "fallback", which is the only way to confirm from the outside that '
      'the model ran rather than being silently bypassed.</p></div></div>'
      '<div style="display:flex;gap:12px;margin-top:13px">'
      f'<div class="num" style="background:{TEAL}">2</div><div>'
      '<b class="hl">Personalisation actually changes the answer.</b>'
      '<p style="font-size:15.5px">Flipping the adventure score from 0.92 to 0.05 changed the '
      'returned list completely, from Very Hard routes to Easy ones. A fixed ordering '
      'dressed up as personalisation would not do that.</p></div></div>'
      '<div style="display:flex;gap:12px;margin-top:13px">'
      f'<div class="num" style="background:{TEAL}">3</div><div>'
      '<b class="hl">The price check behaved exactly as described.</b>'
      '<p style="font-size:15.5px">18,000 rupees flagged as a likely scam at probability 1.0, '
      '4,700 reported as fair, 2,000 raising the below-fair-wage flag with its message &mdash; '
      'while an equally cheap permit correctly raised nothing at all.</p></div></div></div>'
    + '<div class="col" style="width:450px">'
      '<div class="card solid" style="border-top:5px solid ' + AMBER + '">'
      '<h3 style="font-size:19.8px">Verified separately</h3>'
      '<p style="font-size:15.5px"><b class="hl">Live chat.</b> A socket client connected with '
      'a real token from the core engine, joined a booking room, sent a message, and both the '
      'live delivery and the persisted REST history were confirmed with the right participants '
      'attached.</p>'
      '<p style="font-size:15.5px"><b class="hl">Moderation.</b> Verify and dismiss were called '
      'as a staff user and the status changes confirmed in the database, and the same calls '
      'without a token were confirmed to be refused with a 401.</p></div>'
      '<div class="card dark"><p style="font-size:15.5px">This exercise is where all ten '
      'defects in the previous section came from. None was visible from reading the code or '
      'running the tests, and several &mdash; the completely dead chat server, the silently '
      'rejected ML calls &mdash; would have made a live demonstration fail in front of an '
      'examiner. The general lesson, that a system claimed to work should be run in the state '
      'a marker would run it in, is obvious in hindsight and was not obvious at the time.</p></div>'
    + '</div></div></div>'
    + foot("End-to-end verification of the running system"))


add("fig35_limits_future", head(
    "Chapter 6 · Threats to validity and future work",
    "What Constrains These Conclusions, and What Comes Next",
    "Listed in rough order of severity, with the direction each limitation "
    "points toward.")
    + '<div class="body">'
    + '<div class="row" style="margin-bottom:16px">'
    + '<div class="card fill solid" style="border-top:5px solid ' + CRIMSON + '">'
      '<span class="pill no">Threats to validity</span>'
      '<h3 style="margin-top:11px">Seven, in order of how much they matter</h3>'
    + ''.join(
        f'<div style="display:flex;gap:11px;margin-top:11px">'
        f'<div class="num" style="background:{CRIMSON};width:25px;height:25px;font-size:14.9px">{i}</div>'
        f'<div><b style="font-size:16.1px;color:#3E5514">{t}</b>'
        f'<p style="font-size:14.9px;margin-top:2px">{d}</p></div></div>'
        for i, (t, d) in enumerate([
            ("Synthetic data, and this is the serious one",
             "Every result describes a generated world whose correlations were chosen by its "
             "author. The clearest evidence of the limit is the profiling itself: half the "
             "relationships the documentation advertises are absent."),
            ("A structural ceiling on ranking metrics",
             "26 treks behind 2,000 route rows caps route-level precision independently of "
             "model quality. Concept-level metrics reduce this but do not remove it."),
            ("A very short forecasting series",
             "Forty eight monthly observations, twelve of them a pandemic anomaly, and model "
             "selection demonstrably does not replicate across years."),
            ("A small guide-rating sample",
             "4,255 rated pairs and only 984 in the test year, so a 4.8% improvement is "
             "modest relative to that sample."),
            ("All evaluation is offline",
             "No user ever saw a recommendation and acted on it, and offline ranking gains "
             "are known to transfer imperfectly to online behaviour."),
            ("The H3 test is weak",
             "What was measured is that a model which never saw protected attributes still "
             "performs well. That is not the same claim as fairness being affordable."),
            ("Coverage is adequate, not comprehensive",
             "58 tests across four services, concentrated on inference and API contracts "
             "rather than on the training code."),
        ], start=1))
    + '</div>'
    + '<div class="card fill solid" style="border-top:5px solid #6B911C">'
      '<span class="pill ok">Future work</span>'
      '<h3 style="margin-top:11px">Four directions, each following from a finding</h3>'
    + ''.join(
        f'<div style="background:#F4F8EC;border-radius:10px;padding:13px 15px;margin-top:11px">'
        f'<b style="font-size:16.7px;color:#3E5514">{t}</b>'
        f'<p style="font-size:15.1px;margin-top:4px">{d}</p></div>'
        for t, d in [
            ("A real-data pilot &mdash; the most valuable one",
             "Even a small deployment with a handful of licensed guides in one region would "
             "produce genuine interaction data, and would answer the question this project "
             "cannot: whether the relationships that exist in the synthetic world exist in "
             "the real one. The profiling method could be re-run on real data in a few hours, "
             "and the comparison would be informative whichever way it came out."),
            ("An online evaluation",
             "An A/B comparison between the learned ranker and the popularity baseline with "
             "real users would test whether a 1.63 times offline lift corresponds to any "
             "behavioural difference at all."),
            ("A proper test of H3",
             "Apply a fairness intervention that genuinely trades against accuracy &mdash; an "
             "equalised-odds constraint or reweighting &mdash; and measure the loss. Only then "
             "can the claim that fairness is affordable here be made with confidence."),
            ("The discrimination surface verification creates",
             "Following Edelman et al. (2017), a controlled study of whether guide names "
             "influence selection on the platform would establish whether the problem exists "
             "here. It is a necessary precondition for any real deployment."),
        ])
    + '</div></div>'
    + '<div class="card tint"><h3>Deferred product work, documented rather than hidden</h3>'
      '<p style="font-size:16.1px">Cryptographic verification of payment gateway callbacks, an '
      'authenticated admin login, offline map tile pre-download, and on-device chat '
      'translation. Each was classified as a could-have at proposal stage under MoSCoW, and '
      'each fell away when time ran short &mdash; which is the prioritisation working rather '
      'than failing.</p></div>'
    + '</div>'
    + foot("Threats to validity and the work that follows from them"))


# ==========================================================================
# render
# ==========================================================================
def trim(path: Path, pad: int = 30) -> None:
    """Crop trailing whitespace so a figure is only as tall as its content."""
    from PIL import Image

    scale = float(SCALE)
    with Image.open(path) as im:
        rgb = im.convert("RGB")
        w, h = rgb.size
        px = rgb.load()
        last = h - 1
        step = max(w // 240, 1)
        while last > 0 and all(px[x, last] == (255, 255, 255) for x in range(0, w, step)):
            last -= 1
        rgb.crop((0, 0, w, min(h, last + 1 + int(pad * scale)))).save(path, optimize=True)


def render(only: str | None = None) -> None:
    for name, (html, w, h) in FIGS.items():
        if only and only not in name:
            continue
        src = BUILD / f"{name}.html"
        src.write_text(html, encoding="utf-8")
        dest = OUT / f"{name}.png"
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
             f"--force-device-scale-factor={SCALE}", f"--window-size={w},{h}",
             f"--screenshot={dest}", f"file:///{src}"],
            check=True, capture_output=True,
        )
        if not name.startswith("00_"):
            trim(dest)
        print(f"  {name}.png  {dest.stat().st_size // 1024} KB")


if __name__ == "__main__":
    import sys

    sel = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"rendering {len(FIGS)} images -> {OUT}")
    render(sel)
