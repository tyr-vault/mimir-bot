from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class MessageIdempotencyMiddleware(BaseMiddleware):
    """Skip duplicate create handling for the same (user_id, message_id)."""

    def __init__(self, ttl_seconds: float = 120.0) -> None:
        self._ttl = ttl_seconds
        self._seen: dict[tuple[int, int], float] = {}

    def _purge(self, now: float) -> None:
        expired = [key for key, ts in self._seen.items() if now - ts > self._ttl]
        for key in expired:
            del self._seen[key]

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or event.from_user is None:
            return await handler(event, data)

        now = time.monotonic()
        self._purge(now)
        key = (event.from_user.id, event.message_id)
        if key in self._seen:
            data["duplicate_message"] = True
            return None

        self._seen[key] = now
        return await handler(event, data)
