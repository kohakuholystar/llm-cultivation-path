"""星澈助手 · s1:流式初体验 —— 用 stream=True 接收增量 chunk。"""
# 学习契约
# 目标：完成 t03-streaming-ui-s1 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 2 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：create_client(c) -> OpenAI; stream_chat(client, config, question) -> 未标注; main() -> None。
# 技术栈：os, sys, dataclasses, openai；前置条件：在右上角 AI 配置填入自己的 DeepSeek API Key。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
import os
import sys
from dataclasses import dataclass
from openai import OpenAI

if not os.environ.get("OPENAI_API_KEY"):
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)


@dataclass
class APIConfig:
    """连接配置(沿用 t01,字段含义不再重复)。"""
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


def stream_chat(client: OpenAI, config: APIConfig, question: str):
    """流式发送提问,逐块收集增量文本,返回 (完整回复, 块数)。"""
    # TODO: 发起流式请求:
    #   stream = client.chat.completions.create(
    #       model=config.model,
    #       messages=[{"role": "user", "content": question}],
    #       stream=True)          # 关键开关
    # TODO: for chunk in stream 迭代:
    #   delta = chunk.choices[0].delta.content
    #   非空(if delta)才 append 进列表;最后 return "".join(列表), len(列表)
    pass


def main() -> None:
    config = APIConfig.from_env()
    client = create_client(config)
    question = "用一句话夸夸流式输出。"
    print(f"你: {question}")
    reply, n = stream_chat(client, config, question)
    print(f"星澈助手: {reply}")
    print(f"[统计] 共收到 {n} 个增量块,拼接后 {len(reply)} 字")


if __name__ == "__main__":
    main()
