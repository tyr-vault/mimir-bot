from decimal import Decimal

from finance.models import PolicyOutcome, TransactionCandidate
from finance.policy import DEFAULT_POLICY
from finance.validator import validate_candidate


def test_reject_approximate() -> None:
    c = TransactionCandidate(
        raw_text="gastei uns 50 reais no mercado",
        intent_create=True,
        type="expense",
        amounts=[Decimal("50")],
    )
    d = validate_candidate(c, config=DEFAULT_POLICY)
    assert d.outcome == PolicyOutcome.REJECT
    assert "approximate_amount" in d.reasons


def test_clarify_two_amounts() -> None:
    c = TransactionCandidate(
        raw_text="gastei 45 ou 50 reais",
        intent_create=True,
        type="expense",
        amounts=[Decimal("45"), Decimal("50")],
    )
    d = validate_candidate(c, config=DEFAULT_POLICY)
    assert d.outcome == PolicyOutcome.CLARIFY
    assert d.clarify_field == "amount"


def test_clarify_missing_amount() -> None:
    c = TransactionCandidate(
        raw_text="paguei mercado",
        intent_create=True,
        type="expense",
        amounts=[],
        category_hint="mercado",
    )
    d = validate_candidate(c, config=DEFAULT_POLICY)
    assert d.outcome == PolicyOutcome.CLARIFY
    assert d.clarify_field == "amount"


def test_accept_complete() -> None:
    c = TransactionCandidate(
        raw_text="/add -45 lunch Food",
        intent_create=True,
        type="expense",
        amounts=[Decimal("45")],
        category_id="c1",
        category_name="Food",
        date_iso="2026-11-03",
        description="lunch",
    )
    d = validate_candidate(c, config=DEFAULT_POLICY)
    assert d.outcome == PolicyOutcome.ACCEPT
