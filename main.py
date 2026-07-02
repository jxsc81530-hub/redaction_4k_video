import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", "8080"))

async def health(request):
    return web.Response(text="ok")

async def main():
    token = os.environ.get("BOT_TOKEN", "")
    if not token:
        logger.error("BOT_TOKEN not set!")
        return
    logger.info("Token found: %s...", token[:10])

    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info("HTTP server on port %d", PORT)

    bot = Bot(token=token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(message: Message):
        await message.answer("Hello from Railway!")

    @dp.message()
    async def echo(message: Message):
        await message.answer(f"Echo: {message.text}")

    logger.info("Starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
