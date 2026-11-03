from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💸 Today", callback_data="menu:today"),
        InlineKeyboardButton(text="📅 Week", callback_data="menu:week"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Summary", callback_data="menu:summary"),
        InlineKeyboardButton(text="📁 Categories", callback_data="menu:categories"),
    )
    builder.row(
        InlineKeyboardButton(text="➕ /add hint", callback_data="menu:hint_add"),
    )
    builder.row(InlineKeyboardButton(text="❓ Help", callback_data="menu:help"))
    return builder.as_markup()
