from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from finance.models import TransactionPreview
from schemas.api import Draft
from services.drafts import create_transaction_draft_from_preview


def _draft(payload: dict[str, Any], did: str = "d1") -> Draft:
    return Draft.model_validate(
        {
            "id": did,
            "userId": "u",
            "kind": "transaction",
            "status": "pending",
            "payload": payload,
            "source": "bot",
            "confirmedAt": None,
            "rejectedAt": None,
            "createdAt": "2026-11-03T00:00:00Z",
            "updatedAt": "2026-11-03T00:00:00Z",
        }
    )


@pytest.mark.asyncio
async def test_create_from_preview_sends_category_id_and_idempotency() -> None:
    client = AsyncMock()
    client.create_draft.return_value = _draft(
        {"categoryId": "c1", "categoryName": "Food", "type": "expense", "amount": 45}
    )
    preview = TransactionPreview(
        preview_id="p1",
        idempotency_key="p1",
        preview_hash="h",
        type="expense",
        amount=Decimal("45.00"),
        category_id="c1",
        category_name="Food",
        date_iso="2026-11-03",
        description="lunch",
        expires_at=9e12,
    )
    await create_transaction_draft_from_preview(client, preview)
    body = client.create_draft.await_args.args[0]
    assert body.payload.category_id == "c1"
    assert client.create_draft.await_args.kwargs["idempotency_key"] == "p1"
