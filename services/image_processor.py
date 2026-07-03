import logging
import subprocess
import shlex

logger = logging.getLogger(__name__)

PHOTO_PRESETS = {
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4k": (3840, 2160),
}


def enhance_image(src: str, dst: str, target_w: int = 3840, target_h: int = 2160) -> str:
    logger.info("Enhancing image to %dx%d", target_w, target_h)

    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-vf", f"scale={target_w}:{target_h}:flags=lanczos,unsharp=3:3:0.8",
        "-q:v", "2",
        dst,
    ]

    logger.info("Running: %s", shlex.join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        logger.error("ffmpeg stderr:\n%s", result.stderr[-1000:])
        raise RuntimeError(f"ffmpeg failed (code {result.returncode})")

    logger.info("Saved enhanced image: %s", dst)
    return dst
