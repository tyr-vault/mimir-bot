from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from schemas.api import PeriodSummary, Transaction
from services.api_client import ApiErrorKind

WEEKDAY_SHORT = ("Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb")


def format_currency(amount: Decimal | float | int) -> str:
    value = Decimal(str(amount)).quantize(Decimal("0.01"))
    # pt-BR: 1.234,56
    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    integer_part, _, fraction = f"{abs_value:.2f}".partition(".")
    groups: list[str] = []
    while integer_part:
        groups.insert(0, integer_part[-3:])
        integer_part = integer_part[:-3]
    formatted = ".".join(groups) + "," + fraction
    return f"{sign}R$ {formatted}"


def format_help() -> str:
    return "\n".join(
        [
            "💰 Personal Finance",
            "",
            "Creates are saved as drafts — confirm or fix in the dashboard (auto after 3 days).",
            "",
            "Commands:",
            "/start — welcome and this help",
            "/help — list all commands",
            "/add <signed amount> [note...] <category> — transaction draft",
            "    -45 … → expense · 500 … → income",
            "/category <name> — category draft",
            "/categories — list confirmed categories",
            "/today — today's transactions + totals",
            "/week — last 7 days + totals",
            "/summary — current month income / expenses / balance",
            "",
            "Examples:",
            "/add -45 lunch Food",
            "/add 500 salary Income",
            "/category Food",
        ]
    )


def format_draft_saved(
    amount: Decimal,
    category_name: str,
    tx_type: str = "expense",
    note: str | None = None,
) -> str:
    sign = "+" if tx_type == "income" else "-"
    detail = f"{note} · {category_name}" if note and note.strip() else category_name
    return "\n".join(
        [
            f"📝 Draft saved: {sign}{format_currency(amount)} — {detail}",
            "Confirm or edit in the dashboard (auto-confirms in 3 days).",
        ]
    )


def format_category_draft_saved(name: str) -> str:
    return "\n".join(
        [
            f"📝 Category draft saved: {name}",
            "Confirm or edit in the dashboard (auto-confirms in 3 days).",
        ]
    )


def format_category_list(names: list[str]) -> str:
    if not names:
        return "No categories yet. Create one with /category Food"
    return "\n".join(["📁 Categories", "", *[f"• {n}" for n in names]])


def format_category_usage() -> str:
    return "Usage:\n/category Food"


def format_add_usage() -> str:
    return "\n".join(
        [
            "Usage:",
            "/add -45 lunch Food",
            "/add 500 salary Income",
        ]
    )


def format_empty(label: str) -> str:
    return f"No transactions {label}."


def format_malformed_input() -> str:
    return "\n".join(
        [
            "I couldn't understand that.",
            "",
            "Examples:",
            "/add -45 lunch Food",
            "/add 500 salary Income",
        ]
    )


def format_api_error(kind: ApiErrorKind) -> str:
    if kind == "network":
        return "❌ Couldn't reach the finance API."
    if kind == "auth":
        return "❌ Authentication with the finance API failed."
    return "❌ Finance API request failed."


def _display_name(tx: Transaction) -> str:
    if tx.note and tx.note.strip():
        return tx.note.strip()
    return tx.category_name or "—"


def totals_from_transactions(transactions: list[Transaction]) -> dict[str, Decimal]:
    total_income = Decimal("0")
    total_expense = Decimal("0")
    for tx in transactions:
        if tx.type == "income":
            total_income += tx.amount
        else:
            total_expense += tx.amount
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net": total_income - total_expense,
    }


def format_totals_block(
    total_income: Decimal,
    total_expense: Decimal,
    net: Decimal,
) -> list[str]:
    return [
        f"Income:   {format_currency(total_income)}",
        f"Expenses: {format_currency(total_expense)}",
        f"Balance:  {format_currency(net)}",
    ]


def format_today_list(transactions: list[Transaction]) -> str:
    if not transactions:
        return format_empty("today")
    lines = []
    for tx in transactions:
        prefix = "+" if tx.type == "income" else ""
        lines.append(f"{prefix}{format_currency(tx.amount)}  {_display_name(tx)}")
    totals = totals_from_transactions(transactions)
    return "\n".join(
        [
            "💸 Today",
            "",
            *lines,
            "",
            *format_totals_block(
                totals["total_income"],
                totals["total_expense"],
                totals["net"],
            ),
        ]
    )


def _weekday_label(iso_date: str) -> str:
    y, m, d = (int(part) for part in iso_date.split("-"))
    # Match TS getUTCDay (Sunday=0); Python weekday is Monday=0.
    return WEEKDAY_SHORT[(date(y, m, d).weekday() + 1) % 7]


def format_week_summary(transactions: list[Transaction], from_date: str, to_date: str) -> str:
    by_date: dict[str, Decimal] = {}
    cursor = date.fromisoformat(from_date)
    end = date.fromisoformat(to_date)
    while cursor <= end:
        by_date[cursor.isoformat()] = Decimal("0")
        cursor += timedelta(days=1)

    for tx in transactions:
        if tx.type != "expense":
            continue
        key = tx.date[:10]
        by_date[key] = by_date.get(key, Decimal("0")) + tx.amount

    day_lines = [
        f"{_weekday_label(day):<3}  {format_currency(total)}" for day, total in by_date.items()
    ]
    totals = totals_from_transactions(transactions)
    return "\n".join(
        [
            "📅 Last 7 days",
            "",
            *day_lines,
            "",
            *format_totals_block(
                totals["total_income"],
                totals["total_expense"],
                totals["net"],
            ),
        ]
    )


def format_period_summary(summary: PeriodSummary) -> str:
    return "\n".join(
        [
            "📊 Summary",
            "",
            *format_totals_block(summary.total_income, summary.total_expense, summary.net),
        ]
    )
