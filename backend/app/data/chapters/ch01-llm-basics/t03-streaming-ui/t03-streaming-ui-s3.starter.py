"""星澈助手 · s3:打字机界面 —— 逐字渲染,所见即所得。"""
# 学习契约
# 目标：完成 t03-streaming-ui-s3 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 1 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：create_client(c) -> OpenAI; iter_deltas(client, config, question) -> 未标注; typewriter_print(client, config, question, delay) -> str; main() -> None。
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


def iter_deltas(client: OpenAI, config: APIConfig, question: str):
    """产出文本增量的生成器(迭代 stream,逐个 yield 非空 delta.content)。"""
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
    """打字机渲染:逐块打印、立即冲刷,返回完整文本。"""
    parts = []
    for delta in iter_deltas(client, config, question):
        # TODO: 逐块打印且立刻可见:
        #   print(delta, end="", flush=True)
        #   end="" 不换行;flush=True 绕过行缓冲,让增量立刻出现在终端
        #   若 delay > 0,打印后 time.sleep(delay) 放缓节奏
        pass
    print()  # 流结束后补换行,光标归位
    return "".join(parts)


def main() -> None:
    config = APIConfig.from_env()
    client = create_client(config)
    question = "写一段 30 字左右的自我介绍。"
    print(f"你: {question}")
    print("星澈助手: ", end="", flush=True)
    reply = typewriter_print(client, config, question)
    print(f"[完成] 共 {len(reply)} 字")


if __name__ == "__main__":
    main()
