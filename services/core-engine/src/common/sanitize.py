"""Input sanitisation for user-generated text.

We strip any HTML tags from free-text fields (chat messages, itinerary titles,
SOS notes) so stored content can never carry markup that another user's client
might render — a simple, dependency-free guard against stored XSS. Uses Django's
built-in ``strip_tags`` rather than a third-party library to keep the stack lean.
"""
from __future__ import annotations

from django.utils.html import strip_tags


def clean_text(value: str | None) -> str:
    """Return the text with HTML tags removed and surrounding whitespace trimmed."""
    if not value:
        return ""
    return strip_tags(value).strip()
