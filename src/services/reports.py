from __future__ import annotations

from decimal import Decimal
from typing import Any

from presentation.messages import format_currency, format_totals_block, format_week_summary
from schemas.api import Draft, PeriodSummary, Transaction
from services.api_client import MimirApiClient


def _draft_amount(payload: dict[str, Any]) -> Decimal:
    return Decimal(str(payload.get("amount", 0))).quantize(Decimal("0.01"))


def pending_tx_drafts_in_range(
    drafts: list[Draft],
    *,
    from_date: str,
    to_date: str,
) -> list[Draft]:
    result: list[Draft] = []
    for draft in drafts:
        if draft.kind != "transaction" or draft.status != "pending":
            continue
        payload = draft.payload if isinstance(draft.payload, dict) else {}
        day = str(payload.get("date", ""))[:10]
        if from_date <= day <= to_date:
            result.append(draft)
    return result


def format_today_with_drafts(
    transactions: list[Transaction],
    drafts: list[Draft],
) -> str:
    if not transactions and not drafts:
        return "No transactions today."

    lines: list[str] = ["💸 Today", ""]
    total_income = Decimal("0")
    total_expense = Decimal("0")

    for tx in transactions:
        prefix = "+" if tx.type == "income" else ""
        name = (tx.note or "").strip() or tx.category_name or "—"
        lines.append(f"{prefix}{format_currency(tx.amount)}  {name}")
        if tx.type == "income":
            total_income += tx.amount
        else:
            total_expense += tx.amount

    if drafts:
        lines.append("")
        lines.append("Rascunhos pendentes:")
        for draft in drafts:
            payload = draft.payload if isinstance(draft.payload, dict) else {}
            amount = _draft_amount(payload)
            tx_type = payload.get("type", "expense")
            note = (payload.get("note") or "").strip()
            cat = payload.get("categoryName") or "—"
            label = note or cat
            prefix = "+" if tx_type == "income" else ""
            lines.append(f"{prefix}{format_currency(amount)}  {label} (rascunho)")
            if tx_type == "income":
                total_income += amount
            else:
                total_expense += amount

    lines.append("")
    lines.extend(
        format_totals_block(total_income, total_expense, total_income - total_expense)
    )
    lines.append("(totais incluem rascunhos pendentes)")
    return "\n".join(lines)


def format_week_with_drafts(
    transactions: list[Transaction],
    drafts: list[Draft],
    from_date: str,
    to_date: str,
) -> str:
    base = format_week_summary(transactions, from_date, to_date)
    # Recompute totals including drafts
    total_income = Decimal("0")
    total_expense = Decimal("0")
    for tx in transactions:
        if tx.type == "income":
            total_income += tx.amount
        else:
            total_expense += tx.amount
    for draft in drafts:
        payload = draft.payload if isinstance(draft.payload, dict) else {}
        amount = _draft_amount(payload)
        if payload.get("type") == "income":
            total_income += amount
        else:
            total_expense += amount

    draft_lines: list[str] = []
    if drafts:
        draft_lines = ["", "Rascunhos pendentes:"]
        for draft in drafts:
            payload = draft.payload if isinstance(draft.payload, dict) else {}
            amount = _draft_amount(payload)
            day = str(payload.get("date", ""))[:10]
            tx_type = payload.get("type", "expense")
            prefix = "+" if tx_type == "income" else ""
            draft_lines.append(f"{day}  {prefix}{format_currency(amount)} (rascunho)")

    # Replace trailing totals from format_week_summary
    parts = base.split("\n\n")
    head = "\n\n".join(parts[:-1]) if len(parts) > 1 else base
    totals = "\n".join(
        [
            *format_totals_block(total_income, total_expense, total_income - total_expense),
            "(totais incluem rascunhos pendentes)",
        ]
    )
    return "\n".join([head, *draft_lines, "", totals])


def format_summary_with_drafts(summary: PeriodSummary, drafts: list[Draft]) -> str:
    income = summary.total_income
    expense = summary.total_expense
    for draft in drafts:
        payload = draft.payload if isinstance(draft.payload, dict) else {}
        amount = _draft_amount(payload)
        if payload.get("type") == "income":
            income += amount
        else:
            expense += amount
    lines = [
        "📊 Summary",
        "",
        *format_totals_block(income, expense, income - expense),
    ]
    if drafts:
        lines.append(f"Rascunhos pendentes no período: {len(drafts)}")
        lines.append("(totais incluem rascunhos pendentes)")
    return "\n".join(lines)


async def fetch_pending_tx_drafts(api: MimirApiClient) -> list[Draft]:
    drafts = await api.list_drafts(status="pending")
    return [d for d in drafts if d.kind == "transaction"]
