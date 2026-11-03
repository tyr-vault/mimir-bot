from __future__ import annotations

import re
from decimal import Decimal

from finance.date_resolver import resolve_date_hint
from finance.models import TransactionCandidate, TransactionType
from finance.normalize import normalize_for_match, normalize_text
from finance.validator import parse_decimal

ADD_PREFIX = re.compile(r"^/?add\s+(.+)$", re.IGNORECASE)
SIGNED_AMOUNT = re.compile(r"^([+-])?(\d+(?:[.,]\d{1,2})?)\s+(.+)$")
AMOUNT_TOKEN = re.compile(
    r"(?<![.\d])(\d+(?:[.,]\d{1,2})?)\s*(?:reais|real|r\$)?",
    re.IGNORECASE,
)

EXPENSE_VERBS = (
    "gastei",
    "paguei",
    "comprei",
    "desembolsei",
    "debitei",
)
INCOME_VERBS = (
    "recebi",
    "ganhei",
    "entrou",
    "depositei",
)


def _extract_amounts(text: str) -> list[Decimal]:
    found: list[Decimal] = []
    for match in AMOUNT_TOKEN.finditer(text):
        amount = parse_decimal(match.group(1))
        if amount is not None:
            found.append(amount)
    # unique preserve order
    unique: list[Decimal] = []
    for a in found:
        if a not in unique:
            unique.append(a)
    return unique


def _detect_type_and_intent(text: str) -> tuple[bool, TransactionType | None]:
    folded = normalize_for_match(text)
    for verb in EXPENSE_VERBS:
        if re.search(rf"\b{verb}\b", folded):
            return True, "expense"
    for verb in INCOME_VERBS:
        if re.search(rf"\b{verb}\b", folded):
            return True, "income"
    if re.search(r"\bdespesa\b", folded):
        return True, "expense"
    if re.search(r"\breceita\b|\brenda\b", folded):
        return True, "income"
    return False, None


def _strip_noise_for_description(text: str) -> str:
    """Remove common verbs/date words for residual description/category tokens."""
    folded_source = text
    patterns = [
        r"\b(gastei|paguei|comprei|recebi|ganhei)\b",
        r"\b(reais|real|r\$)\b",
        r"\b(hoje|ontem|anteontem)\b",
        r"\bno\b|\bna\b|\bem\b|\bde\b|\bdo\b|\bda\b|\bcom\b",
        r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?",
        r"[+-]?\d+(?:[.,]\d{1,2})?",
    ]
    result = folded_source
    for pat in patterns:
        result = re.sub(pat, " ", result, flags=re.IGNORECASE)
    return normalize_text(result)


def parse_add_structured(payload: str) -> TransactionCandidate:
    """Deterministic /add path: signed amount + [note...] <category>."""
    trimmed = payload.strip()
    match = SIGNED_AMOUNT.match(trimmed)
    if not match:
        return TransactionCandidate(raw_text=f"/add {payload}", intent_create=True)

    sign = match.group(1)
    amount = parse_decimal(match.group(2))
    rest = match.group(3).strip()
    parts = rest.split()
    category_hint = parts[-1] if parts else None
    note = " ".join(parts[:-1]) if len(parts) > 1 else None
    tx_type: TransactionType = "expense" if sign == "-" else "income"

    date_iso, date_hint, ambiguous = resolve_date_hint(trimmed)
    candidate = TransactionCandidate(
        raw_text=f"/add {payload}",
        intent_create=True,
        type=tx_type,
        amounts=[amount] if amount else [],
        category_hint=category_hint,
        description=note,
        date_iso=date_iso,
        date_hint=date_hint,
        flags={"structured_add": True, "ambiguous_date": ambiguous},
    )
    return candidate


def parse_natural_language(text: str) -> TransactionCandidate:
    normalized = normalize_text(text)
    intent, tx_type = _detect_type_and_intent(normalized)
    amounts = _extract_amounts(normalized)
    date_iso, date_hint, ambiguous = resolve_date_hint(normalized)

    residual = _strip_noise_for_description(normalized)
    tokens = residual.split()
    category_hint = tokens[-1] if tokens else None
    description = " ".join(tokens[:-1]) if len(tokens) > 1 else None
    # Prefer merchant/description as residual when category unclear — keep both
    if not description and category_hint:
        # single token: treat as category hint (or description for clarify)
        description = None

    return TransactionCandidate(
        raw_text=normalized,
        intent_create=intent,
        type=tx_type,
        amounts=amounts,
        category_hint=category_hint,
        description=description,
        date_iso=date_iso,
        date_hint=date_hint,
        flags={"ambiguous_date": ambiguous},
    )


def parse_message(text: str) -> TransactionCandidate:
    trimmed = normalize_text(text)
    add_match = ADD_PREFIX.match(trimmed)
    if add_match:
        return parse_add_structured(add_match.group(1))
    return parse_natural_language(trimmed)
