from aiogram.fsm.state import State, StatesGroup


class TransactionCompose(StatesGroup):
    clarifying = State()
    awaiting_confirm = State()
    editing_field = State()
