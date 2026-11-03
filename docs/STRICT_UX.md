# Strict UX — fail-closed transaction processing

## Principle

When in doubt, deny. Never guess amounts, types, or categories. Never persist without explicit Telegram confirmation.

## Outcomes

| Outcome | Meaning |
|---------|---------|
| **ACCEPT** | All required fields valid and unambiguous → show confirmation card |
| **CLARIFY** | Potentially valid; ask **one** missing/ambiguous field |
| **REJECT** | Invalid, approximate, unsupported, or contradictory → stop |

## Policy defaults

- `require_explicit_intent = true`
- `require_amount = true`
- `require_transaction_type = true`
- `require_category = true` (exact match to existing API categories)
- `require_valid_date = true` (defaults to today if no date language)
- `allow_amount_inference = false`
- `allow_category_guessing = false`
- `require_user_confirmation = true`
- `reject_conflicting_values = true`

Accounts are not in the API yet (`require_account = false`).

## Input paths

1. **Structured:** `/add -45 lunch Food` (expense) / `/add 500 salary Income` (income)
2. **Portuguese NL:** `gastei 45 reais no mercado ontem`, `recebi 500 Income`

Rejected examples: `uns 50 reais`, `entre 40 e 60`, messages without create intent.

## Confirmation

1. User sees immutable preview (type, amount, category, date, description).
2. Confirm / Cancel / Edit (edit invalidates previous preview).
3. Confirm → `POST /drafts` with `Idempotency-Key` and **required `categoryId`**.
4. Pending previews expire after `PENDING_TTL_MINUTES` (default 15).
5. Ledger write still happens via dashboard confirm or 3-day auto-confirm.

## Reports

`/today`, `/week`, `/summary` include **pending transaction drafts** in lists and totals, labeled `(rascunho)` / footnote.

## Invariants

1. No draft without Telegram confirmation.
2. No ambiguous/invalid draft.
3. Callbacks verified against allowlisted user + stored preview.
4. Idempotent bot creates (API `Idempotency-Key`).
5. API re-validates `categoryId` for `source=bot` transaction drafts.
