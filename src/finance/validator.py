from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from finance.models import PolicyDecision, PolicyOutcome, TransactionCandidate
from finance.normalize import normalize_for_match
from finance.policy import DEFAULT_POLICY, PolicyConfig

APPROX_PATTERNS = (
    r"\bmais\s+ou\s+menos\b",
    r"\buns\s+\d",
    r"\bumas\s+\d",
    r"\baproximadamente\b",
    r"\bcerca\s+de\b",
    r"\bem\s+torno\s+de\b",
    r"\bentre\s+\d",
)

MULTI_AMOUNT_SEP = re.compile(
    r"\b(\d+(?:[.,]\d{1,2})?)\s*(?:ou|e|/)\s*(\d+(?:[.,]\d{1,2})?)\b",
    re.IGNORECASE,
)


def parse_decimal(raw: str) -> Decimal | None:
    try:
        amount = Decimal(raw.replace(",", "."))
    except InvalidOperation:
        return None
    if amount <= 0:
        return None
    return amount.quantize(Decimal("0.01"))


def has_approximate_language(text: str) -> bool:
    folded = normalize_for_match(text)
    return any(re.search(pat, folded) for pat in APPROX_PATTERNS)


def detect_conflicting_amounts(text: str) -> list[Decimal]:
    match = MULTI_AMOUNT_SEP.search(text)
    if not match:
        return []
    a = parse_decimal(match.group(1))
    b = parse_decimal(match.group(2))
    if a and b and a != b:
        return [a, b]
    return []


def validate_candidate(
    candidate: TransactionCandidate,
    *,
    config: PolicyConfig = DEFAULT_POLICY,
) -> PolicyDecision:
    reasons: list[str] = []

    if has_approximate_language(candidate.raw_text) and not config.allow_amount_inference:
        return PolicyDecision(
            outcome=PolicyOutcome.REJECT,
            candidate=candidate,
            message=(
                "Não registro valores aproximados. Informe um valor exato "
                "(ex.: gastei 45 reais no mercado)."
            ),
            reasons=("approximate_amount",),
        )

    conflicts = detect_conflicting_amounts(candidate.raw_text)
    if conflicts and config.reject_conflicting_values:
        return PolicyDecision(
            outcome=PolicyOutcome.CLARIFY,
            candidate=candidate,
            clarify_field="amount",
            message=(
                f"Encontrei dois valores possíveis: R$ {conflicts[0]} e R$ {conflicts[1]}. "
                "Qual foi o valor correto?"
            ),
            reasons=("multiple_amounts",),
        )

    if config.require_explicit_intent and not candidate.intent_create:
        if config.reject_unsupported_operations:
            return PolicyDecision(
                outcome=PolicyOutcome.REJECT,
                candidate=candidate,
                message=(
                    "Não identifiquei uma intenção clara de registrar uma transação. "
                    "Exemplos: gastei 45 reais no mercado · /add -45 lunch Food"
                ),
                reasons=("missing_intent",),
            )

    if config.require_amount:
        if len(candidate.amounts) == 0:
            return PolicyDecision(
                outcome=PolicyOutcome.CLARIFY,
                candidate=candidate,
                clarify_field="amount",
                message="Não consegui identificar o valor da transação. Quanto foi?",
                reasons=("missing_amount",),
            )
        if len(candidate.amounts) > 1:
            amounts = " e ".join(f"R$ {a}" for a in candidate.amounts)
            return PolicyDecision(
                outcome=PolicyOutcome.CLARIFY,
                candidate=candidate,
                clarify_field="amount",
                message=f"Encontrei vários valores possíveis: {amounts}. Qual foi o valor correto?",
                reasons=("multiple_amounts",),
            )

    if config.require_transaction_type and candidate.type is None:
        return PolicyDecision(
            outcome=PolicyOutcome.CLARIFY,
            candidate=candidate,
            clarify_field="type",
            message="Isso foi uma despesa ou uma receita?",
            reasons=("missing_type",),
        )

    if config.require_valid_date and candidate.date_iso is None:
        if candidate.flags.get("ambiguous_date"):
            return PolicyDecision(
                outcome=PolicyOutcome.CLARIFY,
                candidate=candidate,
                clarify_field="date",
                message=(
                    "Não consegui interpretar a data. "
                    "Qual a data (ex.: hoje, ontem, 02/11/2026)?"
                ),
                reasons=("ambiguous_date",),
            )
        # Default date applied later if missing; only clarify when hint present but unresolved
        if candidate.date_hint:
            return PolicyDecision(
                outcome=PolicyOutcome.CLARIFY,
                candidate=candidate,
                clarify_field="date",
                message=(
                    "Não consegui interpretar a data. "
                    "Qual a data (ex.: hoje, ontem, 02/11/2026)?"
                ),
                reasons=("unresolved_date",),
            )

    if config.require_category:
        if not candidate.category_id:
            if not candidate.category_hint:
                return PolicyDecision(
                    outcome=PolicyOutcome.CLARIFY,
                    candidate=candidate,
                    clarify_field="category",
                    message="Essa entrada foi referente a quê? Informe a categoria "
                    "(veja /categories).",
                    reasons=("missing_category",),
                )
            if candidate.flags.get("unknown_category"):
                return PolicyDecision(
                    outcome=PolicyOutcome.CLARIFY,
                    candidate=candidate,
                    clarify_field="category",
                    message=(
                        f"Não encontrei a categoria “{candidate.category_hint}”. "
                        "Escolha uma categoria existente (/categories) ou crie no dashboard."
                    ),
                    reasons=("unknown_category",),
                )
            if candidate.flags.get("ambiguous_category"):
                return PolicyDecision(
                    outcome=PolicyOutcome.CLARIFY,
                    candidate=candidate,
                    clarify_field="category",
                    message="Encontrei mais de uma categoria possível. Qual delas?",
                    reasons=("ambiguous_category",),
                )
            return PolicyDecision(
                outcome=PolicyOutcome.CLARIFY,
                candidate=candidate,
                clarify_field="category",
                message="Informe a categoria da transação (veja /categories).",
                reasons=("unresolved_category",),
            )

    if reasons:
        return PolicyDecision(
            outcome=PolicyOutcome.REJECT,
            candidate=candidate,
            message="Não foi possível validar a transação.",
            reasons=tuple(reasons),
        )

    return PolicyDecision(
        outcome=PolicyOutcome.ACCEPT,
        candidate=candidate,
        message="ok",
        reasons=(),
    )
