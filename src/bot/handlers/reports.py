from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from presentation.messages import (
    format_api_error,
    format_period_summary,
    format_today_list,
    format_week_summary,
)
from services.api_client import MimirApiClient, MimirApiError
from services.dates import current_month_range, shift_date, today_local

logger = logging.getLogger(__name__)

router = Router(name="reports")


async def _reply_today(target: Message, api: MimirApiClient) -> None:
    try:
        today = today_local()
        transactions = await api.list_transactions(from_date=today, to_date=today)
        await target.answer(format_today_list(transactions))
    except MimirApiError as exc:
        logger.error("[today] %s", exc)
        await target.answer(format_api_error(exc.kind))


async def _reply_week(target: Message, api: MimirApiClient) -> None:
    try:
        to_date = today_local()
        from_date = shift_date(to_date, -6)
        transactions = await api.list_transactions(
            from_date=from_date, to_date=to_date, limit=200
        )
        await target.answer(format_week_summary(transactions, from_date, to_date))
    except MimirApiError as exc:
        logger.error("[week] %s", exc)
        await target.answer(format_api_error(exc.kind))


async def _reply_summary(target: Message, api: MimirApiClient) -> None:
    try:
        from_date, to_date = current_month_range()
        summary = await api.get_summary(from_date=from_date, to_date=to_date)
        await target.answer(format_period_summary(summary))
    except MimirApiError as exc:
        logger.error("[summary] %s", exc)
        await target.answer(format_api_error(exc.kind))


@router.message(Command("today"))
async def cmd_today(message: Message, api: MimirApiClient) -> None:
    await _reply_today(message, api)


@router.message(Command("week"))
async def cmd_week(message: Message, api: MimirApiClient) -> None:
    await _reply_week(message, api)


@router.message(Command("summary"))
async def cmd_summary(message: Message, api: MimirApiClient) -> None:
    await _reply_summary(message, api)


@router.callback_query(F.data == "menu:today")
async def cb_today(callback: CallbackQuery, api: MimirApiClient) -> None:
    await callback.answer()
    if callback.message:
        await _reply_today(callback.message, api)


@router.callback_query(F.data == "menu:week")
async def cb_week(callback: CallbackQuery, api: MimirApiClient) -> None:
    await callback.answer()
    if callback.message:
        await _reply_week(callback.message, api)


@router.callback_query(F.data == "menu:summary")
async def cb_summary(callback: CallbackQuery, api: MimirApiClient) -> None:
    await callback.answer()
    if callback.message:
        await _reply_summary(callback.message, api)
