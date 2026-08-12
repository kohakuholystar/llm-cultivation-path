"""星澈助手 · s2:TTFT 测量 —— 首 token 延迟决定"快"的体感。"""
# 学习契约
# 目标：完成 t03-streaming-ui-s2 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 1 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：create_client(c) -> OpenAI; stream_with_stats(client, config, question) -> 未标注; main() -> None。
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
class StreamStats:
    """一次流式调用的计时数据。"""
    ttft_ms: float      # 首 token 延迟
    total_ms: float     # 总耗时
    chunk_count: int    # 非空增量块数
    char_count: int     # 累计字符数


def stream_with_stats(client: OpenAI, config: APIConfig, question: str):
    """流式提问并测量 TTFT 与总耗时,返回 (完整回复, StreamStats)。"""
    # TODO: start = time.perf_counter() 打点;发起 stream=True 请求并迭代;
    #   首个非空 delta 到达时记 ttft_ms = (time.perf_counter() - start) * 1000;
    #   结束后记 total_ms;拼装 StreamStats 并 return (文本, stats)
    pass


def main() -> None:
    config = APIConfig.from_env()
    client = create_client(config)
    question = "用两句话解释为什么首 token 延迟重要。"
    print(f"你: {question}")
    reply, stats = stream_with_stats(client, config, question)
    print(f"星澈助手: {reply}")
    print(f"TTFT: {stats.ttft_ms:.0f} ms | 总耗时: {stats.total_ms:.0f} ms")


if __name__ == "__main__":
    main()
