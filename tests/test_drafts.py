from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from schemas.api import Draft
from schemas.parse import ParsedTransaction
from services.drafts import create_transaction_draft


def _draft(kind: str, payload: dict[str, Any], did: str = "d1") -> Draft:
    return Draft.model_validate(
        {
            "id": did,
            "userId": "u",
            "kind": kind,
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
async def test_create_draft_without_category_lookup() -> None:
    client = AsyncMock()
    client.create_draft.return_value = _draft(
        "transaction",
        {"categoryName": "Food", "type": "expense", "amount": 45},
    )

    parsed = ParsedTransaction(
        amount=Decimal("45"),
        description="lunch Food",
        type="expense",
        category_hint="Food",
        note="lunch",
    )
    await create_transaction_draft(client, parsed)
    assert client.create_draft.await_count == 1
    client.list_categories.assert_not_called()
    body = client.create_draft.await_args.args[0]
    assert body.kind == "transaction"
    assert body.payload.category_name == "Food"
    assert body.payload.category_id is None
