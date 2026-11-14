"""Readable one-line news headlines (#253, docs/m2-ux-spec.md section 4).

Templates live in the `news_headlines` table. `headline` fills their placeholders from a
news item's corporation and details; a name the item doesn't carry falls back to a plain
generic word ("a corporation", "a town") so every headline still reads as a sentence.
"""

from __future__ import annotations

import string
from collections.abc import Mapping

from .tables import NEWS_HEADLINES

FALLBACK: dict[str, str] = {
    "corp": "a corporation",
    "other_corp": "another corporation",
    "firm_type": "firm",
    "town": "a town",
    "product": "a product",
    "resource": "resource",
}

PLACEHOLDERS = frozenset(FALLBACK)


def fields(template: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(template) if f}


def headline(news_type: int, names: Mapping[str, str | None]) -> str:
    """Headline for `news_type` with `names` (placeholder -> name, None when unknown)."""
    row = NEWS_HEADLINES[int(news_type)]
    filled = {k: names.get(k) or FALLBACK[k] for k in fields(row.template)}
    text = row.template.format(**filled)
    return text[:1].upper() + text[1:]
