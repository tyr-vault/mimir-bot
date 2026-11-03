from __future__ import annotations

import hashlib
import logging
import time
import uuid
from decimal import Decimal

from finance.category_resolver import CategoryRef, resolve_category
from finance.date_resolver import today_local
from finance.models import PolicyDecision, TransactionCandidate, TransactionPreview
from finance.parser import parse_message
from finance.policy import DEFAULT_POLICY, PolicyConfig
from finance.validator import validate_candidate

logger = logging.getLogger(__name__)


def apply_category_resolution(
    candidate: TransactionCandidate,
    categories: list[CategoryRef],
) -> TransactionCandidate:
    result = resolve_category(candidate.category_hint, categories)
    candidate.category_id = result.category_id
    candidate.category_name = result.category_name
    if result.unknown:
        candidate.flags["unknown_category"] = True
    if result.ambiguous:
        candidate.flags["ambiguous_category"] = True
        candidate.flags["category_matches"] = [
            {"id": m.id, "name": m.name} for m in result.matches
        ]
    return candidate


def apply_default_date(candidate: TransactionCandidate) -> TransactionCandidate:
    if candidate.date_iso is None and not candidate.date_hint and not candidate.flags.get(
        "ambiguous_date"
    ):
        candidate.date_iso = today_local().isoformat()
    return candidate


def process_message(
    text: str,
    categories: list[CategoryRef],
    *,
    config: PolicyConfig = DEFAULT_POLICY,
) -> PolicyDecision:
    candidate = parse_message(text)
    candidate = apply_category_resolution(candidate, categories)
    candidate = apply_default_date(candidate)
    decision = validate_candidate(candidate, config=config)
    logger.info(
        "finance_policy outcome=%s reasons=%s",
        decision.outcome.value,
        ",".join(decision.reasons) or "-",
    )
    return decision


def build_preview(
    candidate: TransactionCandidate,
    *,
    ttl_seconds: float = 900.0,
) -> TransactionPreview:
    if (
        candidate.type is None
        or len(candidate.amounts) != 1
        or not candidate.category_id
        or not candidate.category_name
        or not candidate.date_iso
    ):
        raise ValueError("candidate is not ready for preview")

    amount = candidate.amounts[0]
    preview_id = str(uuid.uuid4())
    payload = (
        f"{candidate.type}|{amount}|{candidate.category_id}|"
        f"{candidate.date_iso}|{candidate.description or ''}"
    )
    preview_hash = hashlib.sha256(payload.encode()).hexdigest()
    return TransactionPreview(
        preview_id=preview_id,
        idempotency_key=preview_id,
        preview_hash=preview_hash,
        type=candidate.type,
        amount=amount if isinstance(amount, Decimal) else Decimal(str(amount)),
        category_id=candidate.category_id,
        category_name=candidate.category_name,
        date_iso=candidate.date_iso,
        description=candidate.description,
        expires_at=time.time() + ttl_seconds,
    )
