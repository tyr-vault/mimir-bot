from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

DEFAULT_TZ = ZoneInfo("America/Sao_Paulo")


def today_local(tz: ZoneInfo = DEFAULT_TZ) -> str:
    return datetime.now(tz).date().isoformat()


def shift_date(iso_date: str, days: int) -> str:
    year, month, day = (int(part) for part in iso_date.split("-"))
    return (date(year, month, day) + timedelta(days=days)).isoformat()


def current_month_range(tz: ZoneInfo = DEFAULT_TZ) -> tuple[str, str]:
    today = today_local(tz)
    year, month, _ = today.split("-")
    return f"{year}-{month}-01", today
