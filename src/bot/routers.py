from aiogram import Dispatcher, Router

from bot.handlers import categories, compose, reports, start
from bot.middlewares.idempotency import MessageIdempotencyMiddleware


def setup_routers(dp: Dispatcher) -> None:
    root = Router(name="root")

    compose.router.message.middleware(MessageIdempotencyMiddleware())

    root.include_router(start.router)
    root.include_router(categories.router)
    root.include_router(reports.router)
    root.include_router(compose.router)

    dp.include_router(root)
