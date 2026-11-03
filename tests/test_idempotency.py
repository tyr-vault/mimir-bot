from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from aiogram.types import Chat, Message, User

from bot.middlewares.idempotency import MessageIdempotencyMiddleware


def _message(user_id: int, message_id: int) -> Message:
    return Message(
        message_id=message_id,
        date=0,
        chat=Chat(id=user_id, type="private"),
        from_user=User(id=user_id, is_bot=False, first_name="T"),
        text="200 Food",
    )


@pytest.mark.asyncio
async def test_duplicate_message_skipped() -> None:
    mw = MessageIdempotencyMiddleware(ttl_seconds=60)
    handler = AsyncMock(return_value="ok")
    event = _message(1, 10)

    first = await mw(handler, event, {})
    assert first == "ok"
    assert handler.await_count == 1

    second = await mw(handler, event, {})
    assert second is None
    assert handler.await_count == 1
