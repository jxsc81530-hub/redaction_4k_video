import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    bot_token: str
    max_photo_size: int = 10 * 1024 * 1024  # 10 MB
    max_video_size: int = 50 * 1024 * 1024  # 50 MB
    temp_dir: str = "/tmp/bot_media"

    @classmethod
    def from_env(cls) -> "Config":
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise RuntimeError("BOT_TOKEN environment variable is required")
        return cls(bot_token=token)
