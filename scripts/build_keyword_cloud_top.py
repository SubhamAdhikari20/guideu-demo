"""Condensed keyword cloud for the thesis Keywords section.

The full cloud in build_keyword_cloud.py renders ~260 raw tokens. Supervision
asked for 20-25 keywords, so this variant keeps a curated set of research terms
and drops the generic vocabulary ("Nepal", "system", "work", plain nouns) that
carries no subject meaning.

Word size is still frequency, not preference: each keyword's weight is the
number of times it or its surface variants occur in the finished report, so the
picture stays an honest summary of what the document argues about.

Usage:  python scripts/build_keyword_cloud_top.py [path-to-docx]
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import numpy as np
from docx import Document
from PIL import Image, ImageFilter
from wordcloud import WordCloud

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = REPO_ROOT.parent
OUT = Path(os.environ.get("GUIDEU_THESIS_FIGURES", WORKSPACE_ROOT / "Thesis_Figures"))
DOCX = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    WORKSPACE_ROOT / "Subham_Adhikari_14812262_Final_Thesis_Report.docx"
)

SKIP_STYLES = {"Caption", "table of figures", "TOC Heading", "toc 1", "toc 2", "toc 3"}

# The 24 keywords kept, each with the regexes whose hits count toward it.
# Variants are folded together so "verification"/"licensed" both feed one term.
KEYWORDS: dict[str, list[str]] = {
    "Tourism Platform":        [r"tourism platform", r"travel platform", r"\bplatform\w*"],
    "Guide Verification":      [r"verif\w+", r"licen[cs]\w+"],
    "Recommender Systems":     [r"recommender", r"recommendation"],
    "Decision Support":        [r"\bdecision\w*"],
    "Digital Trust":           [r"\btrust\w*"],
    "Algorithmic Fairness":    [r"fairness", r"\bfair\b(?! wage)"],
    "Anti-Scam Detection":     [r"anti[- ]scam", r"\bscam\w*"],
    "Learning to Rank":        [r"\brank\w*"],
    "Responsible AI":          [r"responsible ai", r"ai ethic\w*", r"ethical\w*", r"\bethics\b"],
    "Agile Development":       [r"\bagile\b", r"\bsprint\w*", r"\bscrum\b"],
    "Price Benchmarking":      [r"benchmark\w*"],
    "Machine Learning":        [r"machine learning", r"\bml\b"],
    "Fair Wage Protection":    [r"fair wage", r"wage flag", r"below fair"],
    "Demand Forecasting":      [r"forecast\w*"],
    "Baseline Comparison":     [r"\bbaseline\w*"],
    "Model Calibration":       [r"calibrat\w+", r"brier"],
    "Tourist Segmentation":    [r"segment\w*", r"clustering", r"\bk-?means\b"],
    "Synthetic Data":          [r"synthetic"],
    "Explainability":          [r"explainab\w+", r"explanation\w*", r"traceab\w+"],
    "Temporal Validation":     [r"temporal", r"holdout", r"held[- ]out"],
    "Information Asymmetry":   [r"asymmetr\w+"],
    "Overcharging":            [r"overcharg\w+"],
    "Cold Start":              [r"cold[- ]start"],
    "Sparsity":                [r"sparsit\w+", r"\bsparse\b"],
    "GDPR":                    [r"\bgdpr\b", r"general data protection"],
}
# Short terms earn their place twice over: each is a distinct argument in the
# report, and the oval's tapered tips need words narrow enough to sit in them.
# "Collaborative Filtering" and "Gradient Boosting" were dropped for the reverse
# reason - the two longest strings with the least support behind them. Cold Start
# stays, so the reason collaborative filtering was ruled out is still on the page.

# Reference palette: olive/green body, teal mid-tones, amber and indigo accents.
DEEP = ["#2C3B22", "#3E5514"]
MID = ["#6B911C", "#00838F", "#4A3AA7"]
BRIGHT = ["#90C226", "#00A0A8", "#C77B00"]


def text_of(path: Path) -> str:
    d = Document(str(path))
    keep, in_refs = [], False
    for p in d.paragraphs:
        st, txt = p.style.name, p.text.strip()
        if st == "Heading 1":
            in_refs = txt.lower().startswith(("reference", "appendix"))
        if in_refs or st in SKIP_STYLES or not txt:
            continue
        keep.append(txt)
    return " ".join(keep)


def frequencies(text: str) -> dict[str, int]:
    flat = re.sub(r"\s+", " ", text.lower())
    return {k: sum(len(re.findall(p, flat)) for p in pats)
            for k, pats in KEYWORDS.items()}


def cloud_mask(w: int, h: int, n: float = 2.0) -> np.ndarray:
    """Ellipse, matching the silhouette of the full 260-word cloud. n=2 is a true
    ellipse; the taper at top and bottom is what makes the block of keywords read
    as an oval, so short terms have to land in the tapered ends."""
    y, x = np.ogrid[:h, :w]
    inside = (np.abs((x - w / 2) / (w / 2 * 0.995)) ** n
              + np.abs((y - h / 2) / (h / 2 * 0.995)) ** n) <= 1.0
    return np.where(inside, 0, 255).astype(np.uint8)


def trim(img: Image.Image, pad: int, bg: str = "white") -> Image.Image:
    """Crop to the inked area, then re-pad evenly, so the figure has no drifting
    empty margin on one side."""
    arr = np.array(img.convert("L"))
    ink = np.argwhere(arr < 250)
    if not len(ink):
        return img
    (y0, x0), (y1, x1) = ink.min(0), ink.max(0) + 1
    core = img.crop((int(x0), int(y0), int(x1), int(y1)))
    out = Image.new("RGB", (core.width + pad * 2, core.height + pad * 2), bg)
    out.paste(core, (pad, pad))
    return out


def make_colour(order: list[str]):
    """Colour by rank tier so the eye reads importance, with the accent hues
    spread through the middle of the list instead of landing at random."""
    rank = {w: i for i, w in enumerate(order)}

    def colour(word, font_size, position, orientation, random_state=None, **kw):
        i = rank.get(word, len(order))
        if i < 3:
            return DEEP[i % len(DEEP)]
        if i < 11:
            return MID[(i - 3) % len(MID)]
        return BRIGHT[(i - 11) % len(BRIGHT)]

    return colour


def main() -> None:
    if not DOCX.is_file():
        raise SystemExit(f"Thesis report not found: {DOCX}. Pass its path as the first argument.")
    OUT.mkdir(parents=True, exist_ok=True)
    freqs = frequencies(text_of(DOCX))
    order = sorted(freqs, key=lambda k: -freqs[k])
    print(f"  {len(order)} keywords, weighted by occurrences in the report")
    for k in order:
        print(f"    {freqs[k]:4d}  {k}")

    # Geometry chosen by sweeping aspect ratio x size-contrast x seed and scoring
    # each layout's row-width profile against a true ellipse: this combination
    # scored highest (0.663) while staying densely filled.
    w, h = 5200, 3600
    windows_font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "segoeuib.ttf"
    wc = WordCloud(
        width=w, height=h, background_color="white", mode="RGB",
        mask=cloud_mask(w, h), max_words=len(freqs),
        min_font_size=48, max_font_size=352,
        prefer_horizontal=1.0, relative_scaling=0.36,
        margin=16, random_state=23,
        font_path=str(windows_font) if windows_font.is_file() else None,
    ).generate_from_frequencies(freqs)
    wc.recolor(color_func=make_colour(order))

    canvas = trim(wc.to_image(), pad=110)
    dest = OUT / "fig00_keywords_top24.png"
    canvas.save(dest, optimize=True, dpi=(300, 300))
    print(f"  fig00_keywords_top24.png  {canvas.size[0]}x{canvas.size[1]}  "
          f"{dest.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
