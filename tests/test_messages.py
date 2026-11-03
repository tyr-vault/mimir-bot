from decimal import Decimal

from presentation.messages import (
    format_currency,
    format_draft_saved,
    format_period_summary,
    format_today_list,
    format_week_summary,
)
from schemas.api import PeriodSummary, Transaction


def _tx(
    *,
    amount: str,
    tx_type: str = "expense",
    note: str | None = "lunch",
    category: str = "Food",
    day: str = "2026-11-03",
) -> Transaction:
    return Transaction.model_validate(
        {
            "id": "1",
            "userId": "u",
            "categoryId": "c",
            "categoryName": category,
            "type": tx_type,
            "amount": amount,
            "date": day,
            "note": note,
            "createdAt": "2026-11-03T00:00:00Z",
            "updatedAt": "2026-11-03T00:00:00Z",
        }
    )


def test_format_currency_pt_br() -> None:
    assert format_currency(Decimal("1503.5")) == "R$ 1.503,50"
    assert format_currency(Decimal("0")) == "R$ 0,00"


def test_format_today_includes_totals() -> None:
    text = format_today_list(
        [
            _tx(amount="100", tx_type="expense"),
            _tx(amount="250", tx_type="income", note="salary"),
        ]
    )
    assert "Income:" in text
    assert "Expenses:" in text
    assert "Balance:" in text
    assert "R$ 250,00" in text


def test_format_week_daily_and_totals() -> None:
    text = format_week_summary(
        [_tx(amount="10", day="2026-11-03")],
        "2026-11-03",
        "2026-11-03",
    )
    assert "Last 7 days" in text
    assert "Income:" in text


def test_format_period_summary() -> None:
    summary = PeriodSummary.model_validate(
        {
            "totalIncome": "1000",
            "totalExpense": "400",
            "net": "600",
            "count": 2,
        }
    )
    text = format_period_summary(summary)
    assert "R$ 1.000,00" in text
    assert "R$ 400,00" in text
    assert "R$ 600,00" in text


def test_format_draft_saved_expense() -> None:
    text = format_draft_saved(Decimal("30"), "Pets", tx_type="expense")
    assert "Despesa" in text
    assert "R$ 30,00" in text
    assert "Pets" in text
