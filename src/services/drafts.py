from __future__ import annotations

from schemas.api import CreateDraftBody, Draft, TransactionDraftPayload
from schemas.parse import ParsedTransaction
from services.api_client import MimirApiClient
from services.dates import today_local


async def create_transaction_draft(
    client: MimirApiClient,
    parsed: ParsedTransaction,
) -> Draft:
    """Create a transaction draft; category is not validated (fix in dashboard)."""
    name = parsed.category_hint.strip() or "Uncategorized"
    payload = TransactionDraftPayload(
        type=parsed.type,
        amount=parsed.amount,
        date=today_local(),
        note=parsed.note,
        category_name=name,
    )
    return await client.create_draft(CreateDraftBody(kind="transaction", payload=payload))


async def create_category_draft(client: MimirApiClient, name: str) -> Draft:
    from schemas.api import CategoryDraftPayload

    trimmed = name.strip()
    if not trimmed:
        raise ValueError("Category name is required")
    return await client.create_draft(
        CreateDraftBody(kind="category", payload=CategoryDraftPayload(name=trimmed))
    )
