from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.middlewares.api_client import ApiClientMiddleware
from bot.middlewares.auth import AllowedUserMiddleware
from bot.routers import setup_routers
from core.config import Settings, get_settings
from core.logging import setup_logging
from services.api_client import MimirApiClient, MimirApiError

logger = logging.getLogger(__name__)


async def _create_api_client(settings: Settings) -> MimirApiClient:
    client = MimirApiClient(
        base_url=settings.api_url,
        email=settings.api_email,
        password=settings.api_password,
        timeout=settings.api_timeout_seconds,
    )
    await client.login()
    logger.info("API client ready (authenticated)")
    return client


def _build_dispatcher(settings: Settings, api: MimirApiClient) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(AllowedUserMiddleware(settings.telegram_allowed_user_id))
    dp.update.middleware(ApiClientMiddleware(api))
    setup_routers(dp)
    return dp


async def run_polling(settings: Settings) -> None:
    api = await _create_api_client(settings)
    bot = Bot(token=settings.telegram_bot_token)
    dp = _build_dispatcher(settings, api)

    try:
        logger.info("Starting Mimir bot (polling)…")
        await dp.start_polling(bot)
    finally:
        await api.aclose()
        await bot.session.close()


async def run_webhook(settings: Settings) -> None:
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
    from aiohttp import web

    if not settings.webhook_url:
        raise RuntimeError("WEBHOOK_URL is required when BOT_MODE=webhook")

    api = await _create_api_client(settings)
    bot = Bot(token=settings.telegram_bot_token)
    dp = _build_dispatcher(settings, api)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)

    async def on_shutdown(_: web.Application) -> None:
        await api.aclose()

    app.on_shutdown.append(on_shutdown)

    await bot.set_webhook(url=f"{settings.webhook_url.rstrip('/')}{settings.webhook_path}")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.webhook_host, port=settings.webhook_port)
    logger.info(
        "Starting Mimir bot (webhook) on %s:%s%s",
        settings.webhook_host,
        settings.webhook_port,
        settings.webhook_path,
    )
    await site.start()
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await bot.session.close()


def main() -> None:
    setup_logging()
    try:
        settings = get_settings()
    except Exception as exc:  # noqa: BLE001
        logger.error("Invalid configuration: %s", exc)
        sys.exit(1)

    try:
        if settings.bot_mode == "webhook":
            asyncio.run(run_webhook(settings))
        else:
            asyncio.run(run_polling(settings))
    except MimirApiError as exc:
        logger.error("Failed to initialize API client: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        with suppress(Exception):
            logger.info("Shutting down…")


if __name__ == "__main__":
    main()
