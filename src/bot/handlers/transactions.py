from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from presentation.messages import (
    format_add_usage,
    format_api_error,
    format_draft_saved,
    format_malformed_input,
)
from services.api_client import MimirApiClient, MimirApiError
from services.drafts import create_transaction_draft
from services.transaction_parser import parse_add_payload

logger = logging.getLogger(__name__)

router = Router(name="transactions")


@router.message(Command("add"))
async def cmd_add(message: Message, command: CommandObject, api: MimirApiClient) -> None:
    payload = (command.args or "").strip()
    if not payload:
        await message.answer(format_add_usage())
        return

    parsed = parse_add_payload(payload)
    if not parsed:
        await message.answer(format_malformed_input())
        return

    try:
        await create_transaction_draft(api, parsed)
        await message.answer(
            format_draft_saved(
                parsed.amount,
                parsed.category_hint,
                parsed.type,
                parsed.note,
            )
        )
    except MimirApiError as exc:
        logger.error("[add] %s", exc)
        await message.answer(format_api_error(exc.kind))
