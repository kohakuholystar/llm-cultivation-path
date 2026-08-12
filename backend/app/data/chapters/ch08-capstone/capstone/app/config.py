"""运行配置只从环境变量读取，绝不把 API Key 写入源码。"""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    model: str
    base_url: str
    api_key: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            model=os.getenv("MODEL_NAME", "deepseek-chat"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
