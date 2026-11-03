from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User

logger = logging.getLogger(__name__)


def _user_from_update(event: Update) -> User | None:
    if event.message and event.message.from_user:
        return event.message.from_user
    if event.edited_message and event.edited_message.from_user:
        return event.edited_message.from_user
    if event.callback_query and event.callback_query.from_user:
        return event.callback_query.from_user
    return None


class AllowedUserMiddleware(BaseMiddleware):
    """Silent ignore for users other than TELEGRAM_ALLOWED_USER_ID."""

    def __init__(self, allowed_user_id: int) -> None:
        self._allowed_user_id = allowed_user_id
        self._warned: set[int] = set()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None and isinstance(event, Update):
            user = _user_from_update(event)

        if user is None or user.id != self._allowed_user_id:
            if user is not None and user.id not in self._warned:
                logger.warning("Ignoring Telegram user_id=%s (not allowlisted)", user.id)
                self._warned.add(user.id)
            return None

        return await handler(event, data)
