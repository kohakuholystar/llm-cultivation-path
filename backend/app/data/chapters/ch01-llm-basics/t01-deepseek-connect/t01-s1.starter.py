"""灵讯通 · s1:配置加载
从环境变量读取 DeepSeek 连接配置,这是整条工具链的第一块基石。
"""
import os
import sys
from dataclasses import dataclass

# 联网前置检查:没有 Key 就给出引导并优雅退出,不让学习者面对 traceback
if not os.environ.get("OPENAI_API_KEY"):
    print("[灵讯通] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)


@dataclass
class APIConfig:
    """一次 LLM 连接所需的全部配置。"""

    api_key: str           # 平台颁发的密钥,只从环境变量读取
    base_url: str          # OpenAI 兼容端点,决定连接哪家厂商
    model: str             # 默认调用的模型名
    timeout: float = 30.0  # 单次请求超时秒数(下一步交给客户端)

    def __post_init__(self) -> None:
        """基础校验:配置有问题应在启动时就炸,而不是等请求发出去。"""
        if not self.api_key:
            raise ValueError("api_key 不能为空")
        if not self.base_url.startswith("http"):
            raise ValueError(f"base_url 非法: {self.base_url}")
        if self.timeout <= 0:
            raise ValueError("timeout 必须为正数")

    @classmethod
    def from_env(cls) -> "APIConfig":
        """从环境变量装配配置,缺省值指向 DeepSeek 官方端点。"""
        # TODO: 从环境变量读取三个值并返回 cls(...)
        # 提示: Key 用 os.environ["OPENAI_API_KEY"] 直接取(顶部已判空);
        #       端点 os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com");
        #       模型 os.environ.get("MODEL_NAME", "deepseek-v4-pro")
        raise NotImplementedError("from_env 尚未实现:请按 TODO 提示读取环境变量并 return cls(...)")

    def masked_key(self) -> str:
        """返回打码后的 Key,日志里只露首尾 4 位。"""
        # TODO: 返回打码 Key。提示: f"{self.api_key[:4]}****{self.api_key[-4:]}"
        raise NotImplementedError("masked_key 尚未实现:请按 TODO 提示返回打码后的 Key")


def main() -> None:
    """加载并(安全地)展示当前配置。"""
    config = APIConfig.from_env()
    print("灵讯通配置加载成功:")
    print(f"  base_url : {config.base_url}")
    print(f"  model    : {config.model}")
    print(f"  api_key  : {config.masked_key()}")  # 只打印打码后的 Key
    print(f"  timeout  : {config.timeout}s")


if __name__ == "__main__":
    main()
