import asyncio
import logging
import os
import uuid

from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile,
)

logger = logging.getLogger(__name__)
router = Router()

PHOTO_PRESETS = {
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4k": (3840, 2160),
}

TEMP_DIR = "/tmp/bot_media"
_photo_storage: dict[str, Message] = {}

os.makedirs(TEMP_DIR, exist_ok=True)


def _quality_keyboard(unique_id: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"imgq:{unique_id}:{label}")]
        for label in ("1080p", "1440p", "4k")
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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
        await callback.answer("Expired. Send the photo again.", show_alert=True)
        return

    await callback.message.delete()
    await callback.answer()

    from services.image_processor import enhance_image

    target_w, target_h = PHOTO_PRESETS[quality]
    status = await original_msg.answer(f"Processing photo → {quality}...")

    try:
        photo = original_msg.photo[-1]
        logger.info("Step 1: getting file info for %s", photo.file_id[:20])

        file = await asyncio.wait_for(
            original_msg.bot.get_file(photo.file_id), timeout=30
        )
        logger.info("Step 2: file path = %s", file.file_path)

        ext = os.path.splitext(file.file_path)[1] or ".jpg"
        src = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}{ext}")
        dst = src.replace(ext, f"_{quality}{ext}")

        logger.info("Step 3: downloading to %s", src)
        await asyncio.wait_for(
            original_msg.bot.download_file(file.file_path, dst=src),
            timeout=60,
        )
        logger.info("Step 4: downloaded, size = %d", os.path.getsize(src))

        logger.info("Step 5: processing with ffmpeg")
        result_path = await asyncio.wait_for(
            asyncio.to_thread(enhance_image, src, dst, target_w, target_h),
            timeout=120,
        )
        logger.info("Step 6: processed, sending result")

        await original_msg.answer_document(
            FSInputFile(result_path),
            caption=f"Enhanced photo ({quality})",
        )
        logger.info("Step 7: sent!")

    except asyncio.TimeoutError:
        logger.error("Timeout during photo processing")
        await original_msg.answer("Processing timed out. Try a smaller photo.")
    except Exception as e:
        logger.exception("Photo processing failed")
        await original_msg.answer(f"Error: {e}")
    finally:
        for p in [src, dst]:
            try:
                os.unlink(p)
            except (OSError, UnboundLocalError):
                pass
        try:
            await status.delete()
        except Exception:
            pass
