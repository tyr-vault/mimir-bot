from __future__ import annotations

from finance.models import TransactionPreview
from schemas.api import CategoryDraftPayload, CreateDraftBody, Draft, TransactionDraftPayload
from services.api_client import MimirApiClient


async def create_transaction_draft_from_preview(
    client: MimirApiClient,
    preview: TransactionPreview,
) -> Draft:
    payload = TransactionDraftPayload(
        type=preview.type,
        amount=preview.amount,
        date=preview.date_iso,
        note=preview.description,
        category_id=preview.category_id,
        category_name=preview.category_name,
    )
    return await client.create_draft(
        CreateDraftBody(kind="transaction", payload=payload),
        idempotency_key=preview.idempotency_key,
    )


async def create_category_draft(
    client: MimirApiClient,
    name: str,
    *,
    idempotency_key: str | None = None,
) -> Draft:
    trimmed = name.strip()
    if not trimmed:
        raise ValueError("Category name is required")
    return await client.create_draft(
        CreateDraftBody(kind="category", payload=CategoryDraftPayload(name=trimmed)),
        idempotency_key=idempotency_key,
    )
