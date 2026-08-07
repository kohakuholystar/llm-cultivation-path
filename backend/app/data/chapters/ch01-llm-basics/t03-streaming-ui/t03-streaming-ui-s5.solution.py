"""灵讯通 · s5:对照实验 —— 同一问题只改 stream 开关,用数据回答流式快在哪。"""
import os
import sys
import time
from dataclasses import dataclass

from openai import OpenAI

MOCK = bool(os.environ.get("MOCK_LLM"))
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[灵讯通] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地演示可设置 MOCK_LLM=1 使用内置假数据)")
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
        return cls(os.environ.get("OPENAI_API_KEY", "sk-mock"),
                   os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                   os.environ.get("MODEL_NAME", "deepseek-v4-pro"))


def create_client(config: APIConfig) -> OpenAI:
    """基于配置创建指向 DeepSeek 的客户端(见 t01-s2)。"""
    return OpenAI(api_key=config.api_key, base_url=config.base_url,
                  timeout=config.timeout, max_retries=0)


@dataclass
class MeasureResult:
    """一次测量的结果:first_ms 是"用户第一次看到内容"的时间。"""

    mode: str
    first_ms: float   # 非流式 = 总耗时;流式 = TTFT
    total_ms: float
    chars: int


def measure_blocking(client: OpenAI, config: APIConfig,
                     question: str) -> MeasureResult:
    """非流式测量:一次性拿到完整回复,first = total。"""
    start = time.perf_counter()
    if MOCK:
        time.sleep(0.5)                     # 模拟"憋大招":生成完才返回
        text = "流式输出把等待拆成了逐字到达的惊喜。"
    else:
        response = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": question}],
        )
        text = response.choices[0].message.content
    total_ms = (time.perf_counter() - start) * 1000
    return MeasureResult("非流式", first_ms=total_ms,
                         total_ms=total_ms, chars=len(text))


def measure_streaming(client: OpenAI, config: APIConfig,
                      question: str) -> MeasureResult:
    """流式测量:first = TTFT,total = 流结束。"""
    start = time.perf_counter()
    ttft_ms = None
    chars = 0
    if MOCK:
        text = "流式输出把等待拆成了逐字到达的惊喜。"
        for i in range(0, len(text), 2):
            time.sleep(0.03)                # 模拟逐块到达
            if ttft_ms is None:
                ttft_ms = (time.perf_counter() - start) * 1000
            chars += len(text[i:i + 2])
    else:
        stream = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": question}],
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if not delta:
                continue
            if ttft_ms is None:
                ttft_ms = (time.perf_counter() - start) * 1000
            chars += len(delta)
    total_ms = (time.perf_counter() - start) * 1000
    return MeasureResult("流式", first_ms=ttft_ms or total_ms,
                         total_ms=total_ms, chars=chars)


def run_experiment(client: OpenAI, config: APIConfig, question: str) -> None:
    """跑对照实验并打印对比报告。"""
    blocking = measure_blocking(client, config, question)
    streaming = measure_streaming(client, config, question)
    print("—— 对照实验结果 ——")
    for r in (blocking, streaming):
        print(f"  {r.mode}: 首字可见 {r.first_ms:.0f}ms | 总耗时 {r.total_ms:.0f}ms | {r.chars} 字")
    if streaming.first_ms > 0:
        ratio = blocking.first_ms / streaming.first_ms
        print(f"结论:完整答案到手时间相近,但流式让首字提前约 {ratio:.1f} 倍可见。")
    print("流式不改变'生成完的时间',它改变的是'等待的体感'。")


def main() -> None:
    """同一问题跑两种模式,输出对比报告。"""
    config = APIConfig.from_env()
    client = create_client(config)
    question = "用一句话说明流式输出的好处。"
    print(f"实验问题: {question}")
    run_experiment(client, config, question)


if __name__ == "__main__":
    main()
