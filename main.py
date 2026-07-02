import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

async def main():
    token = os.environ.get("BOT_TOKEN", "")
    logger.info("Starting bot with token: %s...", token[:10] if token else "MISSING")
    
    bot = Bot(token=token)
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(message: Message):
        await message.answer("Hello from Railway!")

    @dp.message()
    async def echo(message: Message):
        await message.answer(f"Echo: {message.text}")

    logger.info("Polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
