from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from schemas.parse import ParsedTransaction, TransactionType

ADD_PREFIX = re.compile(r"^/?add\s+(.+)$", re.IGNORECASE)
SIGNED_AMOUNT_DESC = re.compile(r"^([+-])?(\d+(?:[.,]\d{1,2})?)\s+(.+)$")


def parse_amount(raw: str) -> Decimal | None:
    try:
        amount = Decimal(raw.replace(",", "."))
    except InvalidOperation:
        return None
    if amount <= 0:
        return None
    return amount.quantize(Decimal("0.01"))


def split_category_hint(text: str) -> tuple[str, str | None]:
    parts = [part for part in text.strip().split() if part]
    if not parts:
        return "", None
    if len(parts) == 1:
        return parts[0], None
    return parts[-1], " ".join(parts[:-1])


def _build(amount: Decimal, description: str, tx_type: TransactionType) -> ParsedTransaction:
    category_hint, note = split_category_hint(description)
    return ParsedTransaction(
        amount=amount,
        description=description,
        type=tx_type,
        category_hint=category_hint,
        note=note,
    )


def parse_add_payload(text: str) -> ParsedTransaction | None:
    """
    Parse /add payload: signed amount + rest.
    Negative → expense; positive (optional +) → income.
    """
    trimmed = text.strip()
    if not trimmed:
        return None

    match = SIGNED_AMOUNT_DESC.match(trimmed)
    if not match:
        return None

    sign = match.group(1)
    amount = parse_amount(match.group(2))
    description = match.group(3).strip()
    if amount is None or not description:
        return None

    tx_type: TransactionType = "expense" if sign == "-" else "income"
    return _build(amount, description, tx_type)


def parse_transaction(text: str) -> ParsedTransaction | None:
    """Only /add … is accepted for creates."""
    trimmed = text.strip()
    add_match = ADD_PREFIX.match(trimmed)
    if not add_match:
        return None
    return parse_add_payload(add_match.group(1))
