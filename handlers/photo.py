import asyncio
import logging
import os
import tempfile
import uuid

from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile,
)

from config import Config
from services.image_processor import enhance_image, PHOTO_PRESETS

logger = logging.getLogger(__name__)
router = Router()

_photo_storage: dict[str, Message] = {}


def _quality_keyboard(unique_id: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"imgq:{unique_id}:{label}")]
        for label in ("1080p", "1440p", "4k")
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def _process_photo(message: Message, quality: str):
    config = Config.from_env()
    target_w, target_h = PHOTO_PRESETS[quality]

    status = await message.answer(f"Processing photo → {quality}...")

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    ext = os.path.splitext(file.file_path)[1] or ".jpg"

    with tempfile.NamedTemporaryFile(suffix=ext, dir=config.temp_dir, delete=False) as f:
        src = f.name
        await message.bot.download_file(file.file_path, dst=f)

    dst = src.replace(ext, f"_{quality}{ext}")

    try:
        result_path = await asyncio.get_event_loop().run_in_executor(
            None, enhance_image, src, dst, target_w, target_h
        )
        await message.answer_document(
            FSInputFile(result_path),
            caption=f"Enhanced photo ({quality})",
        )
    except Exception as e:
        logger.exception("Photo processing failed")
        await message.answer(f"Error: {e}")
    finally:
        for p in (src, dst):
            try:
                os.unlink(p)
            except OSError:
                pass
        await status.delete()


@router.message(F.photo)
async def handle_photo(message: Message):
    unique_id = uuid.uuid4().hex[:8]
    _photo_storage[unique_id] = message

    await message.answer(
        "Select output quality for your photo:",
        reply_markup=_quality_keyboard(unique_id),
    )


@router.callback_query(F.data.startswith("imgq:"))
async def handle_quality_choice(callback: CallbackQuery):
    parts = callback.data.split(":")
    unique_id = parts[1]
    quality = parts[2]

    original_msg = _photo_storage.pop(unique_id, None)

    if original_msg is None:
        await callback.answer("Original photo expired. Send the photo again.", show_alert=True)
        return

    await callback.message.delete()
    await callback.answer()

    await _process_photo(original_msg, quality)
