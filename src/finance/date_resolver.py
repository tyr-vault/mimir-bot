from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from finance.normalize import normalize_for_match

DEFAULT_TZ = ZoneInfo("America/Sao_Paulo")

EXPLICIT_DATE = re.compile(
    r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b",
)


def today_local(tz: ZoneInfo = DEFAULT_TZ) -> date:
    return datetime.now(tz).date()


def resolve_date_hint(
    text: str,
    *,
    tz: ZoneInfo = DEFAULT_TZ,
) -> tuple[str | None, str | None, bool]:
    """
    Returns (iso_date, hint_token, ambiguous).
    If no date language, returns (None, None, False) — caller may default to today.
    """
    folded = normalize_for_match(text)
    today = today_local(tz)

    if re.search(r"\bhoje\b", folded):
        return today.isoformat(), "hoje", False
    if re.search(r"\bontem\b", folded):
        return (today - timedelta(days=1)).isoformat(), "ontem", False
    if re.search(r"\banteontem\b", folded):
        return (today - timedelta(days=2)).isoformat(), "anteontem", False

    match = EXPLICIT_DATE.search(text)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year_raw = match.group(3)
        year = today.year if year_raw is None else int(year_raw)
        if year < 100:
            year += 2000
        try:
            resolved = date(year, month, day)
        except ValueError:
            return None, match.group(0), True
        return resolved.isoformat(), match.group(0), False

    return None, None, False
