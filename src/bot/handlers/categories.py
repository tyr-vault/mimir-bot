from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from presentation.messages import (
    format_api_error,
    format_category_draft_saved,
    format_category_list,
    format_category_usage,
)
from services.api_client import MimirApiClient, MimirApiError
from services.drafts import create_category_draft

logger = logging.getLogger(__name__)

router = Router(name="categories")


@router.message(Command("category"))
async def cmd_category(message: Message, command: CommandObject, api: MimirApiClient) -> None:
    name = (command.args or "").strip()
    if not name:
        await message.answer(format_category_usage())
        return
    try:
        draft = await create_category_draft(api, name)
        draft_name = draft.payload.get("name", name) if isinstance(draft.payload, dict) else name
        await message.answer(format_category_draft_saved(str(draft_name)))
    except MimirApiError as exc:
        logger.error("[category] %s", exc)
        await message.answer(format_api_error(exc.kind))
    except ValueError:
        await message.answer(format_category_usage())


@router.message(Command("categories"))
async def cmd_categories(message: Message, api: MimirApiClient) -> None:
    try:
        categories = await api.list_categories()
        names = sorted((c.name for c in categories), key=str.casefold)
        await message.answer(format_category_list(names))
    except MimirApiError as exc:
        logger.error("[categories] %s", exc)
        await message.answer(format_api_error(exc.kind))


@router.callback_query(F.data == "menu:categories")
async def cb_categories(callback: CallbackQuery, api: MimirApiClient) -> None:
    await callback.answer()
    if not callback.message:
        return
    try:
        categories = await api.list_categories()
        names = sorted((c.name for c in categories), key=str.casefold)
        await callback.message.answer(format_category_list(names))
    except MimirApiError as exc:
        logger.error("[categories] %s", exc)
        await callback.message.answer(format_api_error(exc.kind))
