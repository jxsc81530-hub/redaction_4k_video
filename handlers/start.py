from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()

HELP_TEXT = (
    "<b>Photo &amp; Video Quality Enhancer Bot</b>\n\n"
    "Send me a photo or video and I will enhance its quality.\n\n"
    "<b>Photos:</b> upscaled to 4K with sharpening.\n"
    "<b>Videos:</b> up to 4K 120 FPS with quality presets.\n\n"
    "<b>Commands:</b>\n"
    "/start - show this message\n"
    "/help - show this message"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(HELP_TEXT)
