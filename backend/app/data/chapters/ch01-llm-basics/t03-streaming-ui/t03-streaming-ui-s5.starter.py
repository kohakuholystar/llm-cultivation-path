"""星澈助手 · s5:对照实验 —— 流式 vs 非流式,用数据说话。"""
# 学习契约
# 目标：完成 t03-streaming-ui-s5 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 1 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：create_client(c) -> OpenAI; measure_blocking(client, config, question) -> MeasureResult; measure_streaming(client, config, question) -> MeasureResult; run_experiment(client, config, question) -> None。
# 技术栈：os, sys, time, dataclasses, openai；前置条件：在右上角 AI 配置填入自己的 DeepSeek API Key。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
import os
import sys
import time
from dataclasses import dataclass
from openai import OpenAI

if not os.environ.get("OPENAI_API_KEY"):
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)


@dataclass
class APIConfig:
    """连接配置(沿用 t01)。"""
    api_key: str
    base_url: str
    model: str
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "APIConfig":
        return cls(os.environ["OPENAI_API_KEY"],
                   os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                   os.environ.get("MODEL_NAME", "deepseek-v4-pro"))


def create_client(c: APIConfig) -> OpenAI:  # 同 t01-s2
    return OpenAI(api_key=c.api_key, base_url=c.base_url,
                  timeout=c.timeout, max_retries=0)


@dataclass
class MeasureResult:
    """一次测量的结果:first_ms 是"用户第一次看到内容"的时间。"""
    mode: str
    first_ms: float   # 非流式 = 总耗时;流式 = TTFT
    total_ms: float
    chars: int


def measure_blocking(client: OpenAI, config: APIConfig, question: str) -> MeasureResult:
    """非流式测量:一次性拿到完整回复。"""
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=config.model,
        messages=[{"role": "user", "content": question}],
    )
    text = response.choices[0].message.content
    total_ms = (time.perf_counter() - start) * 1000
    return MeasureResult("非流式", first_ms=total_ms, total_ms=total_ms, chars=len(text))


def measure_streaming(client: OpenAI, config: APIConfig, question: str) -> MeasureResult:
    """流式测量:first = TTFT,total = 流结束。"""
    # TODO: start = time.perf_counter();发起 stream=True 请求并迭代;
    #   首个非空 delta 记 ttft_ms,累计 chars;结束记 total_ms;
    #   return MeasureResult("流式", ttft_ms, total_ms, chars)
    pass


def run_experiment(client: OpenAI, config: APIConfig, question: str) -> None:
    blocking = measure_blocking(client, config, question)
    streaming = measure_streaming(client, config, question)
    print(f"{blocking.mode}: 首字 {blocking.first_ms:.0f}ms 总 {blocking.total_ms:.0f}ms")
    print(f"{streaming.mode}: 首字 {streaming.first_ms:.0f}ms 总 {streaming.total_ms:.0f}ms")


def main() -> None:
    config = APIConfig.from_env()
    client = create_client(config)
    run_experiment(client, config, "用一句话说明流式输出的好处。")


if __name__ == "__main__":
    main()
