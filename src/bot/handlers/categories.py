from __future__ import annotations

import logging
import uuid

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from presentation.messages import (
    format_api_error,
    format_cancelled,
    format_category_draft_saved,
    format_category_list,
    format_category_usage,
)
from services.api_client import MimirApiClient, MimirApiError
from services.drafts import create_category_draft

logger = logging.getLogger(__name__)

router = Router(name="categories")


class CategoryCompose(StatesGroup):
    awaiting_confirm = State()


@router.message(Command("category"))
async def cmd_category(
    message: Message,
    command: CommandObject,
    state: FSMContext,
) -> None:
    name = (command.args or "").strip()
    if not name:
        await message.answer(format_category_usage())
        return
    token = str(uuid.uuid4())
    await state.set_state(CategoryCompose.awaiting_confirm)
    await state.update_data(category_name=name, category_token=token)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Confirmar", callback_data=f"cat:confirm:{token}"),
        InlineKeyboardButton(text="❌ Cancelar", callback_data="cat:cancel"),
    )
    await message.answer(
        f"Confira a categoria:\n\n📁 Nome: {name}\n\nDeseja registrar como rascunho?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("cat:confirm:"))
async def cb_category_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    api: MimirApiClient,
) -> None:
    await callback.answer()
    token = (callback.data or "").split(":")[-1]
    data = await state.get_data()
    if data.get("category_token") != token:
        if callback.message:
            await callback.message.answer("Confirmação inválida ou expirada.")
        await state.clear()
        return
    name = data.get("category_name")
    if not name:
        await state.clear()
        return
    try:
        draft = await create_category_draft(api, name, idempotency_key=token)
        draft_name = draft.payload.get("name", name) if isinstance(draft.payload, dict) else name
        await state.clear()
        if callback.message:
            await callback.message.answer(format_category_draft_saved(str(draft_name)))
        logger.info("audit category_confirm")
    except MimirApiError as exc:
        logger.error("[category] %s", exc)
        if callback.message:
            await callback.message.answer(format_api_error(exc.kind))


@router.callback_query(F.data == "cat:cancel")
async def cb_category_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    if callback.message:
        await callback.message.answer(format_cancelled())


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
