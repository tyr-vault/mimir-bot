from decimal import Decimal

from services.transaction_parser import parse_add_payload, parse_transaction


def test_add_negative_is_expense() -> None:
    parsed = parse_add_payload("-45 lunch Food")
    assert parsed is not None
    assert parsed.type == "expense"
    assert parsed.amount == Decimal("45.00")
    assert parsed.category_hint == "Food"
    assert parsed.note == "lunch"


def test_add_positive_is_income() -> None:
    parsed = parse_add_payload("500 salary Income")
    assert parsed is not None
    assert parsed.type == "income"
    assert parsed.amount == Decimal("500.00")


def test_add_explicit_plus_is_income() -> None:
    parsed = parse_add_payload("+500 salary Income")
    assert parsed is not None
    assert parsed.type == "income"


def test_single_token_category() -> None:
    parsed = parse_add_payload("-200 Groceries")
    assert parsed is not None
    assert parsed.category_hint == "Groceries"
    assert parsed.note is None


def test_comma_decimal() -> None:
    parsed = parse_add_payload("-12,5 lunch Food")
    assert parsed is not None
    assert parsed.amount == Decimal("12.50")


def test_invalid_amount() -> None:
    assert parse_add_payload("0 lunch Food") is None
    assert parse_add_payload("abc Food") is None


def test_parse_transaction_requires_add_prefix() -> None:
    assert parse_transaction("45 lunch Food") is None
    parsed = parse_transaction("/add -45 lunch Food")
    assert parsed is not None
    assert parsed.type == "expense"
