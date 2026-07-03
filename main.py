import asyncio
import logging
import os
import sys

from aiohttp import web

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", "8080"))
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

logger.info("Python %s", sys.version)
logger.info("BOT_TOKEN: %s", "SET" if BOT_TOKEN else "MISSING")


async def health(request):
    return web.Response(text="ok")


async def main():
    os.makedirs("/tmp/bot_media", exist_ok=True)

    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    logger.info("Healthcheck on port %d", PORT)

    logger.info("Importing aiogram...")
    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    logger.info("Importing handlers...")
    from handlers.start import router as start_router
    from handlers.photo import router as photo_router
    from handlers.video import router as video_router
    logger.info("All imports OK")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(photo_router)
    dp.include_router(video_router)

    logger.info("Starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
