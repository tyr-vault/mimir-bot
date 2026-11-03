from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Collapse whitespace; keep numbers/dates; strip accents for matching helpers."""
    cleaned = text.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def fold_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_for_match(text: str) -> str:
    return fold_accents(normalize_text(text)).lower()
