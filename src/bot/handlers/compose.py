from __future__ import annotations

import logging
from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.confirmation import (
    category_pick_keyboard,
    confirmation_keyboard,
    type_pick_keyboard,
)
from bot.states.transaction_compose import TransactionCompose
from core.config import get_settings
from finance.category_resolver import CategoryRef
from finance.engine import build_preview, process_message
from finance.models import PolicyOutcome, TransactionCandidate
from finance.validator import parse_decimal
from presentation.messages import (
    format_api_error,
    format_cancelled,
    format_clarify,
    format_draft_saved,
    format_expired,
    format_reject,
    format_transaction_preview,
)
from services.api_client import MimirApiClient, MimirApiError
from services.drafts import create_transaction_draft_from_preview
from services.pending_store import pending_store

logger = logging.getLogger(__name__)

router = Router(name="compose")


async def _categories(api: MimirApiClient) -> list[CategoryRef]:
    cats = await api.list_categories()
    return [CategoryRef(id=c.id, name=c.name) for c in cats]


def _candidate_from_fsm(data: dict) -> TransactionCandidate:
    amounts = [Decimal(a) for a in data.get("amounts", [])]
    return TransactionCandidate(
        raw_text=data.get("raw_text", ""),
        intent_create=True,
        type=data.get("type"),
        amounts=amounts,
        category_hint=data.get("category_hint"),
        category_id=data.get("category_id"),
        category_name=data.get("category_name"),
        date_iso=data.get("date_iso"),
        description=data.get("description"),
        flags=data.get("flags") or {},
    )


def _fsm_from_candidate(candidate: TransactionCandidate) -> dict:
    return {
        "raw_text": candidate.raw_text,
        "type": candidate.type,
        "amounts": [str(a) for a in candidate.amounts],
        "category_hint": candidate.category_hint,
        "category_id": candidate.category_id,
        "category_name": candidate.category_name,
        "date_iso": candidate.date_iso,
        "description": candidate.description,
        "flags": candidate.flags,
    }


async def _offer_preview(
    message: Message,
    state: FSMContext,
    candidate: TransactionCandidate,
    user_id: int,
) -> None:
    settings = get_settings()
    preview = build_preview(
        candidate,
        ttl_seconds=settings.pending_ttl_minutes * 60,
    )
    pending_store.invalidate_user(user_id)
    pending_store.put(user_id, preview)
    await state.set_state(TransactionCompose.awaiting_confirm)
    await state.update_data(preview_id=preview.preview_id, **_fsm_from_candidate(candidate))
    await message.answer(
        format_transaction_preview(
            tx_type=preview.type,
            amount=preview.amount,
            category_name=preview.category_name,
            date_iso=preview.date_iso,
            description=preview.description,
        ),
        reply_markup=confirmation_keyboard(preview.preview_id),
    )
    logger.info("audit accept preview_id=%s", preview.preview_id)


async def _handle_decision(
    message: Message,
    state: FSMContext,
    api: MimirApiClient,
    text: str,
) -> None:
    cats = await _categories(api)
    decision = process_message(text, cats)

    if decision.outcome == PolicyOutcome.REJECT:
        logger.info("audit reject reasons=%s", ",".join(decision.reasons))
        await state.clear()
        await message.answer(format_reject(decision.message))
        return

    if decision.outcome == PolicyOutcome.CLARIFY:
        logger.info("audit clarify field=%s", decision.clarify_field)
        await state.set_state(TransactionCompose.clarifying)
        await state.update_data(
            clarify_field=decision.clarify_field,
            **_fsm_from_candidate(decision.candidate),
        )
        if decision.clarify_field == "type":
            await message.answer(
                format_clarify(decision.message),
                reply_markup=type_pick_keyboard(),
            )
        elif decision.clarify_field == "category":
            options = [(c.id, c.name) for c in cats]
            await message.answer(
                format_clarify(decision.message),
                reply_markup=category_pick_keyboard(options, "clarify"),
            )
        else:
            await message.answer(format_clarify(decision.message))
        return

    await _offer_preview(message, state, decision.candidate, message.from_user.id)  # type: ignore[union-attr]


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    preview_id = data.get("preview_id")
    if preview_id:
        pending_store.invalidate(preview_id)
    await state.clear()
    logger.info("audit cancel")
    await message.answer(format_cancelled())


@router.message(Command("add"))
async def cmd_add(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    api: MimirApiClient,
) -> None:
    payload = (command.args or "").strip()
    if not payload:
        await message.answer(
            format_clarify(
                "Uso: /add -45 lunch Food  ou  /add 500 salary Income"
            )
        )
        return
    await _handle_decision(message, state, api, f"/add {payload}")


@router.message(F.text & ~F.text.startswith("/"), StateFilter(None))
async def free_text(
    message: Message,
    state: FSMContext,
    api: MimirApiClient,
) -> None:
    text = message.text or ""
    await _handle_decision(message, state, api, text)


@router.message(TransactionCompose.clarifying, F.text)
async def clarify_reply(message: Message, state: FSMContext, api: MimirApiClient) -> None:
    if (message.text or "").startswith("/"):
        return
    data = await state.get_data()
    field = data.get("clarify_field")
    candidate = _candidate_from_fsm(data)
    text = (message.text or "").strip()

    if field == "amount":
        amount = parse_decimal(text.replace("R$", "").replace("reais", "").strip())
        if amount is None:
            await message.answer(format_clarify("Informe um valor positivo válido (ex.: 45,50)."))
            return
        candidate.amounts = [amount]
    elif field == "date":
        from finance.date_resolver import resolve_date_hint

        iso, hint, amb = resolve_date_hint(text)
        if not iso or amb:
            await message.answer(
                format_clarify("Data inválida. Use hoje, ontem ou DD/MM/AAAA.")
            )
            return
        candidate.date_iso = iso
        candidate.date_hint = hint
        candidate.flags["ambiguous_date"] = False
    elif field == "description":
        candidate.description = text
    elif field == "category":
        candidate.category_hint = text
        candidate.category_id = None
        candidate.category_name = None
        candidate.flags.pop("unknown_category", None)
        cats = await _categories(api)
        from finance.engine import apply_category_resolution

        candidate = apply_category_resolution(candidate, cats)
    else:
        await message.answer(format_clarify("Envie o dado solicitado ou /cancel."))
        return

    cats = await _categories(api)
    from finance.engine import apply_default_date
    from finance.validator import validate_candidate

    candidate = apply_default_date(candidate)
    decision = validate_candidate(candidate)
    if decision.outcome == PolicyOutcome.ACCEPT:
        await _offer_preview(message, state, candidate, message.from_user.id)  # type: ignore[union-attr]
        return
    if decision.outcome == PolicyOutcome.CLARIFY:
        await state.update_data(
            clarify_field=decision.clarify_field,
            **_fsm_from_candidate(decision.candidate),
        )
        await message.answer(format_clarify(decision.message))
        return
    await state.clear()
    await message.answer(format_reject(decision.message))


@router.callback_query(F.data.startswith("tx:type:"))
async def cb_type(callback: CallbackQuery, state: FSMContext, api: MimirApiClient) -> None:
    await callback.answer()
    tx_type = callback.data.split(":")[-1]  # type: ignore[union-attr]
    if tx_type not in ("expense", "income"):
        return
    data = await state.get_data()
    candidate = _candidate_from_fsm(data)
    candidate.type = tx_type  # type: ignore[assignment]
    cats = await _categories(api)
    from finance.engine import apply_default_date
    from finance.validator import validate_candidate

    candidate = apply_default_date(candidate)
    decision = validate_candidate(candidate)
    if not callback.message:
        return
    if decision.outcome == PolicyOutcome.ACCEPT:
        await _offer_preview(
            callback.message, state, candidate, callback.from_user.id
        )
        return
    if decision.outcome == PolicyOutcome.CLARIFY:
        await state.set_state(TransactionCompose.clarifying)
        await state.update_data(
            clarify_field=decision.clarify_field,
            **_fsm_from_candidate(decision.candidate),
        )
        msg = format_clarify(decision.message)
        if decision.clarify_field == "category":
            options = [(c.id, c.name) for c in cats]
            await callback.message.answer(msg, reply_markup=category_pick_keyboard(options, "c"))
        else:
            await callback.message.answer(msg)
        return
    await state.clear()
    await callback.message.answer(format_reject(decision.message))


@router.callback_query(F.data.startswith("tx:cat:"))
async def cb_category(callback: CallbackQuery, state: FSMContext, api: MimirApiClient) -> None:
    await callback.answer()
    category_id = callback.data.split(":")[-1]  # type: ignore[union-attr]
    cats = await _categories(api)
    match = next((c for c in cats if c.id == category_id), None)
    if not match:
        if callback.message:
            await callback.message.answer(format_reject("Categoria inválida."))
        return
    if not callback.message:
        return
    data = await state.get_data()
    candidate = _candidate_from_fsm(data)
    candidate.category_id = match.id
    candidate.category_name = match.name
    candidate.category_hint = match.name
    candidate.flags.pop("unknown_category", None)
    candidate.flags.pop("ambiguous_category", None)
    from finance.engine import apply_default_date
    from finance.validator import validate_candidate

    candidate = apply_default_date(candidate)
    decision = validate_candidate(candidate)
    if decision.outcome == PolicyOutcome.ACCEPT:
        await _offer_preview(callback.message, state, candidate, callback.from_user.id)
        return
    if decision.outcome == PolicyOutcome.CLARIFY:
        await state.update_data(
            clarify_field=decision.clarify_field,
            **_fsm_from_candidate(decision.candidate),
        )
        await callback.message.answer(format_clarify(decision.message))
        return
    await state.clear()
    await callback.message.answer(format_reject(decision.message))


@router.callback_query(F.data.startswith("tx:confirm:"))
async def cb_confirm(callback: CallbackQuery, state: FSMContext, api: MimirApiClient) -> None:
    await callback.answer()
    preview_id = callback.data.split(":")[-1]  # type: ignore[union-attr]
    user_id = callback.from_user.id
    preview = pending_store.get(preview_id, user_id)
    if preview is None:
        await state.clear()
        if callback.message:
            await callback.message.answer(format_expired())
        return
    data = await state.get_data()
    if data.get("preview_id") != preview_id:
        if callback.message:
            await callback.message.answer(format_reject("Confirmação inválida."))
        return
    try:
        await create_transaction_draft_from_preview(api, preview)
        logger.info("audit confirm preview_id=%s", preview_id)
        pending_store.invalidate(preview_id)
        await state.clear()
        if callback.message:
            await callback.message.answer(
                format_draft_saved(
                    preview.amount,
                    preview.category_name,
                    preview.type,
                    preview.description,
                )
            )
    except MimirApiError as exc:
        logger.error("audit confirm_failed %s", exc)
        if callback.message:
            await callback.message.answer(format_api_error(exc.kind))


@router.callback_query(F.data.startswith("tx:cancel:"))
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = (callback.data or "").split(":")
    if len(parts) >= 3 and parts[2] != "clarify":
        pending_store.invalidate(parts[2])
    await state.clear()
    logger.info("audit cancel")
    if callback.message:
        await callback.message.answer(format_cancelled())


@router.callback_query(F.data.startswith("tx:edit:"))
async def cb_edit(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    # tx:edit:amount:preview_id
    parts = (callback.data or "").split(":")
    if len(parts) < 4:
        return
    field, preview_id = parts[2], parts[3]
    pending_store.invalidate(preview_id)
    await state.set_state(TransactionCompose.clarifying)
    await state.update_data(clarify_field=field, preview_id=None)
    prompts = {
        "amount": "Qual o valor correto?",
        "category": "Qual a categoria? (veja /categories)",
        "date": "Qual a data?",
        "description": "Qual a descrição?",
    }
    if callback.message:
        await callback.message.answer(
            format_clarify(prompts.get(field, "Envie o novo valor."))
        )
