from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from bot.keyboards.main_menu import main_menu_keyboard
from presentation.messages import format_help

router = Router(name="start")


@router.message(CommandStart())
@router.message(Command("help"))
async def cmd_start(message: Message) -> None:
    await message.answer(format_help(), reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(format_help(), reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:hint_add")
async def cb_hint_add(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Exemplos (sempre com confirmação):\n"
            "`/add -45 lunch Food`\n"
            "`gastei 45 reais no Food`\n"
            "`/add 500 salary Income`",
            parse_mode="Markdown",
        )
