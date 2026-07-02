import asyncio
import logging
import os
import traceback

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", "8080"))


async def health(request):
    return web.Response(text="ok")


async def main():
    token = os.environ.get("BOT_TOKEN", "")
    logger.info("BOT_TOKEN: %s", "SET" if token else "MISSING")
    os.makedirs("/tmp/bot_media", exist_ok=True)

    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    logger.info("Healthcheck on port %d", PORT)

    try:
        from handlers import start, photo, video
        logger.info("Handlers imported OK")
    except Exception as e:
        logger.error("Import error: %s\n%s", e, traceback.format_exc())
        return

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(photo.router)
    dp.include_router(video.router)

    logger.info("Bot starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
