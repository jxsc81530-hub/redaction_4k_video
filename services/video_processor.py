import logging
import subprocess
import shlex

logger = logging.getLogger(__name__)


def enhance_video(src: str, dst: str, preset: dict) -> str:
    w = preset["width"]
    h = preset["height"]
    fps = preset["fps"]
    crf = preset["crf"]
    audio_bitrate = preset.get("audio_bitrate", "192k")

    logger.info("Enhancing video to %dx%d @ %d fps (crf=%d, audio=%s)", w, h, fps, crf, audio_bitrate)

    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-vf", f"scale={w}:{h}:flags=lanczos:force_original_aspect_ratio=decrease",
        "-r", str(fps),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", str(crf),
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        "-movflags", "+faststart",
        "-threads", "1",
        dst,
    ]

    logger.info("Running: %s", shlex.join(cmd))
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=600
    )

    if result.returncode != 0:
        logger.error("ffmpeg stderr:\n%s", result.stderr[-2000:])
        raise RuntimeError(f"ffmpeg failed (code {result.returncode})")

    logger.info("Saved enhanced video: %s", dst)
    return dst
