"""灵讯通 · s3:打字机界面
把增量文本逐字刷到终端:print(end="", flush=True) 加节奏控制。
"""
import os
import sys
import time
from dataclasses import dataclass

from openai import OpenAI

MOCK = bool(os.environ.get("MOCK_LLM"))
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[灵讯通] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地演示可设置 MOCK_LLM=1 使用内置假回复)")
    sys.exit(0)


@dataclass
class APIConfig:
    """一次 LLM 连接所需的全部配置(沿用 t01-s1)。"""

    api_key: str
    base_url: str
    model: str
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "APIConfig":
        return cls(
            api_key=os.environ.get("OPENAI_API_KEY", "sk-mock"),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
            model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
            timeout=float(os.environ.get("LLM_TIMEOUT", "30")),
        )


def create_client(config: APIConfig) -> OpenAI:
    """基于配置创建指向 DeepSeek 的客户端(见 t01-s2)。"""
    return OpenAI(api_key=config.api_key, base_url=config.base_url,
                  timeout=config.timeout, max_retries=0)


def iter_deltas(client: OpenAI, config: APIConfig, question: str):
    """统一产出文本增量:真实模式迭代 SDK 流,MOCK 模式切片假回复。"""
    if MOCK:
        reply = "流式输出逐字到达,打字机让它像真人书写一样浮现。"
        for i in range(0, len(reply), 2):
            yield reply[i:i + 2]
        return
    stream = client.chat.completions.create(
        model=config.model,
        messages=[{"role": "user", "content": question}],
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def typewriter_print(client: OpenAI, config: APIConfig, question: str,
                     delay: float = 0.0) -> str:
    """打字机渲染:逐块打印、立即冲刷,返回完整文本。

    end="" 不换行;flush=True 绕过行缓冲,让每个增量立刻可见;
    delay 可人为放缓节奏,让 MOCK 演示也有"人味"。
    """
    parts = []
    for delta in iter_deltas(client, config, question):
        print(delta, end="", flush=True)  # 关键:不换行 + 立即冲刷
        parts.append(delta)
        if delay:
            time.sleep(delay)
    print()  # 流结束后补一个换行,光标归位
    return "".join(parts)


def main() -> None:
    """打字机效果演示:回复在终端逐字浮现。"""
    config = APIConfig.from_env()
    client = create_client(config)
    question = "写一段 30 字左右的自我介绍。"
    print(f"你: {question}")
    print("灵讯通: ", end="", flush=True)
    start = time.perf_counter()
    # MOCK 演示时放慢节奏,真实模式跟紧 API 的推送速度
    reply = typewriter_print(client, config, question,
                             delay=0.05 if MOCK else 0.0)
    elapsed = time.perf_counter() - start
    print(f"[完成] 共 {len(reply)} 字,用时 {elapsed:.1f}s,全程逐字可见。")


if __name__ == "__main__":
    main()
