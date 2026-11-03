from decimal import Decimal

from finance.parser import parse_message


def test_add_negative_expense() -> None:
    c = parse_message("/add -45 lunch Food")
    assert c.intent_create
    assert c.type == "expense"
    assert c.amounts == [Decimal("45.00")]
    assert c.category_hint == "Food"
    assert c.description == "lunch"


def test_add_positive_income() -> None:
    c = parse_message("/add 500 salary Income")
    assert c.type == "income"
    assert c.amounts == [Decimal("500.00")]


def test_nl_expense_gastei() -> None:
    c = parse_message("gastei 45 reais no mercado ontem")
    assert c.intent_create
    assert c.type == "expense"
    assert c.amounts == [Decimal("45.00")]
    assert c.date_iso is not None  # ontem resolved


def test_nl_income_recebi() -> None:
    c = parse_message("recebi 500")
    assert c.intent_create
    assert c.type == "income"
    assert c.amounts == [Decimal("500.00")]


def test_no_intent() -> None:
    c = parse_message("olá tudo bem")
    assert not c.intent_create
