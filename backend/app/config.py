"""应用配置(pydantic-settings)。

从环境变量 / .env 读取。优先读项目根目录的 .env,再读 cwd 的 .env(覆盖)。
M0-3 定义所有配置项,M1 课程生成器与 M2 沙箱会用到。
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py → backend/app → backend → 项目根
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_PROJECT_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === 后端服务 ===
    backend_host: str = "0.0.0.0"
    backend_port: int = 4200
    cors_origins: str = "http://localhost:3200"

    # === 代码执行沙箱 (M2) ===
    sandbox_image: str = "llmquest-sandbox:latest"
    sandbox_ml_image: str = "llmquest-sandbox-ml:latest"
    sandbox_max_concurrency: int = 5
    sandbox_default_timeout: int = 10
    sandbox_enabled: bool = True

    # === 公网防护(云端启用; 空/0 = 关闭, 公开库与本地默认休眠) ===
    # 访问口令(邀请码), 逗号分隔多个; 空 = 关闭门槛
    access_codes: str = ""
    # 邀请码真源文件(服务器独立私有文件, 600; 缺失/损坏时回退 access_codes)
    invite_codes_path: str = "/etc/llmquest/invite-codes.json"
    # 每 IP 每分钟沙箱运行次数上限; 0 = 不限
    sandbox_rate_limit: int = 10
    # 并发槽位满时排队等待上限(秒), 超时返回 503 沙箱繁忙而不是无限挂起
    sandbox_queue_timeout: int = 20

    # === 课程数据 ===
    data_dir: str = "app/data"

    # === 课程生成器 (M1) / 默认 DeepSeek 配置 ===
    # 学习者联网沙箱必须提交自己的 Key；runner 不会读取这里的 Key 作为兜底。
    # 模型名对照(见 https://api-docs.deepseek.com/quick_start/pricing):
    #   deepseek-v4-pro   最新对话模型(默认)
    #   deepseek-v4-flash 更快更便宜
    #   deepseek-chat / deepseek-reasoner  旧名, 2026-07-24 弃用
    openai_api_key: str = ""
    openai_base_url: str = "https://api.deepseek.com"
    generator_model: str = "deepseek-v4-pro"

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS 来源按逗号拆分。"""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def access_codes_list(self) -> list[str]:
        """访问口令按逗号拆分; 空列表 = 不启用门槛。"""
        return [c.strip() for c in self.access_codes.split(",") if c.strip()]

    @property
    def project_root(self) -> Path:
        return _PROJECT_ROOT

    @property
    def backend_root(self) -> Path:
        """backend/ 目录绝对路径。"""
        return _PROJECT_ROOT / "backend"

    @property
    def data_path(self) -> Path:
        """课程数据目录(backend/app/data)。"""
        return self.backend_root / self.data_dir


settings = Settings()
