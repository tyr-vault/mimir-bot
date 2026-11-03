from decimal import Decimal

from finance.category_resolver import CategoryRef
from finance.engine import process_message
from finance.models import PolicyOutcome

CATS = [
    CategoryRef(id="c-food", name="Food"),
    CategoryRef(id="c-inc", name="Income"),
    CategoryRef(id="c-merc", name="Mercado"),
]


def test_structured_add_accept() -> None:
    d = process_message("/add -45 lunch Food", CATS)
    assert d.outcome == PolicyOutcome.ACCEPT
    assert d.candidate.category_id == "c-food"
    assert d.candidate.type == "expense"


def test_unknown_category_clarify() -> None:
    d = process_message("/add -30 Pets", CATS)
    assert d.outcome == PolicyOutcome.CLARIFY
    assert d.clarify_field == "category"


def test_nl_recebi_missing_category() -> None:
    d = process_message("recebi 500", CATS)
    assert d.outcome == PolicyOutcome.CLARIFY
    assert d.clarify_field == "category"


def test_reject_unsupported() -> None:
    d = process_message("bom dia", CATS)
    assert d.outcome == PolicyOutcome.REJECT


def test_nl_with_known_category() -> None:
    d = process_message("gastei 45 no Mercado", CATS)
    assert d.outcome == PolicyOutcome.ACCEPT
    assert d.candidate.amounts == [Decimal("45.00")]
    assert d.candidate.category_id == "c-merc"
