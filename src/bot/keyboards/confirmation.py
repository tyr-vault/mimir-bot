from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def confirmation_keyboard(preview_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Confirmar", callback_data=f"tx:confirm:{preview_id}"),
        InlineKeyboardButton(text="❌ Cancelar", callback_data=f"tx:cancel:{preview_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Editar valor", callback_data=f"tx:edit:amount:{preview_id}"),
        InlineKeyboardButton(
            text="✏️ Editar categoria", callback_data=f"tx:edit:category:{preview_id}"
        ),
    )
    return builder.as_markup()


def category_pick_keyboard(
    categories: list[tuple[str, str]],
    preview_token: str,
) -> InlineKeyboardMarkup:
    """categories: list of (id, name). preview_token reserved for future use."""
    _ = preview_token
    builder = InlineKeyboardBuilder()
    for cid, name in categories[:12]:
        builder.row(InlineKeyboardButton(text=name, callback_data=f"tx:cat:{cid}"))
    builder.row(InlineKeyboardButton(text="❌ Cancelar", callback_data="tx:cancel:clarify"))
    return builder.as_markup()


def type_pick_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💸 Despesa", callback_data="tx:type:expense"),
        InlineKeyboardButton(text="💰 Receita", callback_data="tx:type:income"),
    )
    builder.row(InlineKeyboardButton(text="❌ Cancelar", callback_data="tx:cancel:clarify"))
    return builder.as_markup()
