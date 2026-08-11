"""Keyword cloud for the thesis Keywords section.

Reads the finished report, strips the front matter, references and captions,
then renders a word cloud in the report's own palette. Word size is straight
frequency, so the picture is an honest summary of what the document is about
rather than a hand-picked list.

Usage:  python scripts/build_keyword_cloud.py <path-to-docx>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
from docx import Document
from PIL import Image
from wordcloud import STOPWORDS, WordCloud

OUT = Path(r"C:\Users\Asus\BSc_Computing\Projects\final_year_project\Thesis_Figures")
DOCX = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    r"C:\Users\Asus\BSc_Computing\Projects\final_year_project"
    r"\Subham_Adhikari_14812262_Final_Thesis_Report.docx")

SKIP_STYLES = {"Caption", "table of figures", "TOC Heading", "toc 1", "toc 2", "toc 3"}

# Words that are frequent but say nothing about the subject.
EXTRA_STOP = {
    "one", "two", "three", "four", "five", "six", "ten", "also", "would", "could",
    "rather", "much", "many", "made", "make", "makes", "well", "still", "even",
    "way", "ways", "thing", "things", "used", "using", "use", "uses", "however",
    "therefore", "chapter", "figure", "table", "section", "report", "thesis",
    "project", "et", "al", "et al", "per", "cent", "number", "numbers", "first",
    "second", "third", "every", "never", "always", "something", "anything",
    "nothing", "somebody", "anybody", "means", "mean", "given", "give", "gives",
    "shows", "show", "shown", "found", "find", "took", "take", "taken", "put",
    "got", "get", "gets", "say", "says", "said", "actually", "really", "quite",
    "enough", "less", "least", "though", "although", "whether", "within",
    "without", "across", "toward", "towards", "onto", "upon", "already", "yet",
    "back", "part", "parts", "point", "points", "kind", "sort", "case", "cases",
    "reason", "reasons", "result", "results", "work", "works", "worked", "run",
    "runs", "ran", "look", "looks", "looked", "need", "needs", "needed", "set",
    "sets", "come", "comes", "came", "went", "goes", "going", "know", "knows",
    "known", "seen", "see", "saw", "turn", "turned", "turns", "far", "long",
    "good", "better", "best", "worse", "worst", "high", "higher", "low", "lower",
    "small", "large", "big", "whole", "own", "same", "different", "another",
    "several", "single", "particular", "specific", "certain", "real", "actual",
}


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


def ellipse_mask(w: int, h: int) -> np.ndarray:
    y, x = np.ogrid[:h, :w]
    cy, cx = h / 2, w / 2
    inside = ((x - cx) / (cx * 0.985)) ** 2 + ((y - cy) / (cy * 0.985)) ** 2 <= 1
    return np.where(inside, 0, 255).astype(np.uint8)


PALETTE = ["#3E5514", "#6B911C", "#90C226", "#00838F", "#00A0A8",
           "#C77B00", "#4A3AA7", "#2C3B22"]


def colour(word, font_size, position, orientation, random_state=None, **kw):
    # Bigger words get the darker, heavier end of the palette.
    idx = 0 if font_size > 120 else 1 if font_size > 80 else 3 if font_size > 55 else \
        (random_state.randint(0, len(PALETTE)) if random_state else 2)
    return PALETTE[idx % len(PALETTE)]


def main() -> None:
    text = text_of(DOCX)
    stop = set(STOPWORDS) | EXTRA_STOP
    wc = WordCloud(
        width=2600, height=1750, background_color="white", mask=ellipse_mask(2600, 1750),
        stopwords=stop, max_words=260, min_font_size=13, max_font_size=190,
        prefer_horizontal=0.92, relative_scaling=0.48, collocations=True,
        collocation_threshold=24, margin=6, random_state=20240519,
        font_path=r"C:\Windows\Fonts\segoeuib.ttf",
    ).generate(text)
    wc.recolor(color_func=colour, random_state=20240519)

    img = wc.to_image()
    canvas = Image.new("RGB", (img.width + 90, img.height + 90), "white")
    canvas.paste(img, (45, 45))
    dest = OUT / "fig00_keywords.png"
    canvas.save(dest, optimize=True)
    print(f"  fig00_keywords.png  {dest.stat().st_size // 1024} KB")
    print("  top terms:", ", ".join(list(wc.words_)[:22]))


if __name__ == "__main__":
    main()
