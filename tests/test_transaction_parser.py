"""Legacy parser module retained for /add helpers used by older imports — prefer finance.parser."""

from finance.parser import parse_message


def test_add_via_finance_parser() -> None:
    c = parse_message("/add -45 lunch Food")
    assert c.type == "expense"
    assert c.category_hint == "Food"
