from aiogram import Dispatcher, Router

from bot.handlers import categories, reports, start, transactions
from bot.middlewares.idempotency import MessageIdempotencyMiddleware


def setup_routers(dp: Dispatcher) -> None:
    root = Router(name="root")

    # Idempotency only for /add creates
    transactions.router.message.middleware(MessageIdempotencyMiddleware())

    root.include_router(start.router)
    root.include_router(categories.router)
    root.include_router(reports.router)
    root.include_router(transactions.router)

    dp.include_router(root)
