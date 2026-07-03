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

RESOLUTIONS = {
    "720p": {"width": 1280, "height": 720, "crf": 20},
    "1080p": {"width": 1920, "height": 1080, "crf": 18},
    "1440p": {"width": 2560, "height": 1440, "crf": 17},
    "4k": {"width": 3840, "height": 2160, "crf": 15},
}

FPS_OPTIONS = ["30", "60", "120"]
AUDIO_OPTIONS = ["128k", "192k", "256k", "320k"]

TEMP_DIR = "/tmp/bot_media"
_video_storage: dict[str, Message] = {}

os.makedirs(TEMP_DIR, exist_ok=True)


def _resolution_keyboard(unique_id: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"vidres:{unique_id}:{label}")]
        for label in ("720p", "1080p", "1440p", "4k")
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _fps_keyboard(unique_id: str, resolution: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"{fps} FPS", callback_data=f"vidfps:{unique_id}:{resolution}:{fps}")]
        for fps in FPS_OPTIONS
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _audio_keyboard(unique_id: str, resolution: str, fps: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"{bitrate} bitrate", callback_data=f"vidaud:{unique_id}:{resolution}:{fps}:{bitrate}")]
        for bitrate in AUDIO_OPTIONS
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.video)
async def handle_video(message: Message):
    unique_id = uuid.uuid4().hex[:8]
    _video_storage[unique_id] = message

    await message.answer(
        "Select output resolution:",
        reply_markup=_resolution_keyboard(unique_id),
    )


@router.callback_query(F.data.startswith("vidres:"))
async def handle_resolution_choice(callback: CallbackQuery):
    parts = callback.data.split(":")
    unique_id = parts[1]
    resolution = parts[2]

    await callback.message.edit_text(
        f"Resolution: {resolution}\nSelect FPS:",
        reply_markup=_fps_keyboard(unique_id, resolution),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("vidfps:"))
async def handle_fps_choice(callback: CallbackQuery):
    parts = callback.data.split(":")
    unique_id = parts[1]
    resolution = parts[2]
    fps = parts[3]

    await callback.message.edit_text(
        f"Resolution: {resolution}\nFPS: {fps}\nSelect audio quality:",
        reply_markup=_audio_keyboard(unique_id, resolution, fps),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("vidaud:"))
async def handle_audio_choice(callback: CallbackQuery):
    parts = callback.data.split(":")
    unique_id = parts[1]
    resolution = parts[2]
    fps = int(parts[3])
    audio_bitrate = parts[4]

    original_msg = _video_storage.pop(unique_id, None)
    if original_msg is None:
        await callback.answer("Expired. Send the video again.", show_alert=True)
        return

    await callback.message.delete()
    await callback.answer()

    from services.video_processor import enhance_video

    res = RESOLUTIONS[resolution]
    preset = {**res, "fps": fps, "audio_bitrate": audio_bitrate}
    status = await original_msg.answer(f"Processing video → {resolution} @ {fps} FPS, audio {audio_bitrate}...")

    src = None
    dst = None
    try:
        video = original_msg.video
        logger.info("Step 1: getting video file info")
        file = await asyncio.wait_for(
            original_msg.bot.get_file(video.file_id), timeout=30
        )
        logger.info("Step 2: file path = %s", file.file_path)

        src = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}.mp4")
        dst = src.replace(".mp4", f"_{resolution}_{fps}fps_{audio_bitrate}.mp4")

        logger.info("Step 3: downloading to %s", src)
        await asyncio.wait_for(
            original_msg.bot.download_file(file.file_path, dst=src),
            timeout=120,
        )
        logger.info("Step 4: downloaded, size = %d", os.path.getsize(src))

        logger.info("Step 5: processing with ffmpeg")
        result_path = await asyncio.wait_for(
            asyncio.to_thread(enhance_video, src, dst, preset),
            timeout=600,
        )
        logger.info("Step 6: processed, sending")

        await original_msg.answer_document(
            FSInputFile(result_path),
            caption=f"Enhanced video ({resolution} @ {fps} FPS, audio {audio_bitrate})",
        )
        logger.info("Step 7: sent!")

    except asyncio.TimeoutError:
        logger.error("Timeout during video processing")
        await original_msg.answer("Processing timed out. Try a smaller video or lower quality.")
    except Exception as e:
        logger.exception("Video processing failed")
        await original_msg.answer(f"Error: {e}")
    finally:
        for p in [src, dst]:
            if p:
                try:
                    os.unlink(p)
                except OSError:
                    pass
        try:
            await status.delete()
        except Exception:
            pass
