from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

TransactionType = Literal["expense", "income"]
ClarifyField = Literal["amount", "type", "category", "date", "description"]


class PolicyOutcome(Enum):
    ACCEPT = "ACCEPT"
    CLARIFY = "CLARIFY"
    REJECT = "REJECT"


@dataclass
class TransactionCandidate:
    raw_text: str
    intent_create: bool = False
    type: TransactionType | None = None
    amounts: list[Decimal] = field(default_factory=list)
    category_hint: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    date_iso: str | None = None
    date_hint: str | None = None
    description: str | None = None
    currency: str = "BRL"
    flags: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyDecision:
    outcome: PolicyOutcome
    candidate: TransactionCandidate
    clarify_field: ClarifyField | None = None
    message: str = ""
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class TransactionPreview:
    preview_id: str
    idempotency_key: str
    preview_hash: str
    type: TransactionType
    amount: Decimal
    category_id: str
    category_name: str
    date_iso: str
    description: str | None
    expires_at: float  # monotonic / epoch seconds
    currency: str = "BRL"
