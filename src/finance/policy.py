from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyConfig:
    require_explicit_intent: bool = True
    require_amount: bool = True
    require_transaction_type: bool = True
    require_category: bool = True
    require_valid_date: bool = True
    require_account: bool = False  # no accounts in API v1
    allow_amount_inference: bool = False
    allow_category_guessing: bool = False
    allow_implicit_transaction_creation: bool = False
    require_user_confirmation: bool = True
    reject_conflicting_values: bool = True
    reject_unsupported_operations: bool = True


DEFAULT_POLICY = PolicyConfig()
