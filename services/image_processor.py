import logging
from PIL import Image, ImageFilter, ImageEnhance

logger = logging.getLogger(__name__)

PHOTO_PRESETS = {
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4k": (3840, 2160),
}


def enhance_image(src: str, dst: str, target_w: int = 3840, target_h: int = 2160) -> str:
    img = Image.open(src)

    orig_w, orig_h = img.size
    logger.info("Source image: %dx%d", orig_w, orig_h)

    if orig_w < target_w or orig_h < target_h:
        ratio = min(target_w / orig_w, target_h / orig_h)
        new_size = (int(orig_w * ratio), int(orig_h * ratio))
        img = img.resize(new_size, Image.LANCZOS)
        logger.info("Upscaled to %dx%d", *new_size)

    img = ImageEnhance.Sharpness(img).enhance(1.4)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = ImageEnhance.Color(img).enhance(1.05)

    img = img.filter(ImageFilter.DETAIL)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.save(dst, quality=95)
    logger.info("Saved enhanced image: %s", dst)
    return dst
