"""黑糖资料室 · 对话记忆策略 · s3：用 LangChain 完成可验证的学习任务。"""
import os
import sys

import tiktoken
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

if not os.environ.get("OPENAI_API_KEY"):
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key，然后重新运行。")
    sys.exit(0)

SCRIPT = ["我叫阿岩，想做一份轻量海报。", "我主要用手机查看，标题别太长。", "预算三百元以内。", "海报加入一个‘山’字。", "搭配一个深色边框。"]
LOCAL_REPLIES = ["移动端海报，标题会相应缩短。", "三百元以内没有问题。", "加入‘山’字，主题会更明确。", "深色边框很沉稳，搭配合适。"]

try:
    ENCODING = tiktoken.get_encoding("cl100k_base")
except Exception:
    ENCODING = None


def get_chat_model() -> ChatOpenAI:
    return ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"), base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"), api_key=os.environ["OPENAI_API_KEY"], temperature=0.3)


def fetch_real_anchor(model: ChatOpenAI) -> str:
    return model.invoke([HumanMessage(content="你是内容制作顾问。用一句不超过二十字的话回应：" + SCRIPT[0])]).content


def make_memory(backend: str) -> InMemoryChatMessageHistory:
    if backend in {"buffer", "window"}:
        return InMemoryChatMessageHistory()
    raise ValueError(f"未知记忆后端: {backend}")


def count_tokens(messages) -> int:
    if ENCODING is not None:
        return sum(len(ENCODING.encode(message.content)) + 4 for message in messages)
    return sum(len(message.content) + 4 for message in messages)


class ForgeAdvisor:
    def __init__(self, memory: InMemoryChatMessageHistory, backend: str):
        self.memory = memory
        self.backend = backend

    def record_turn(self, user_input: str, reply: str) -> None:
        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(reply)
        if self.backend == "window":
            k = 2
            self.memory.messages = self.memory.messages[-2 * k:]


def run_dialogue(advisor: ForgeAdvisor, real_anchor: str) -> list[int]:
    """每轮后的 token 均来自本地消息列表，不会触发额外网络请求。"""
    growth = []
    advisor.record_turn(SCRIPT[0], real_anchor)
    growth.append(count_tokens(advisor.memory.messages))
    for user_input, reply in zip(SCRIPT[1:], LOCAL_REPLIES, strict=True):
        advisor.record_turn(user_input, reply)
        growth.append(count_tokens(advisor.memory.messages))
    return growth


def compare_backends() -> None:
    real_anchor = fetch_real_anchor(get_chat_model())
    print("本次真实 DeepSeek 调用：1 次；后续四轮为本地记忆回放。")
    print(f"剧本共 {len(SCRIPT)} 轮，Window 后端 k=2\n")
    for backend in ("buffer", "window"):
        growth = run_dialogue(ForgeAdvisor(make_memory(backend), backend), real_anchor)
        print(f"  后端 {backend:>6}: 逐轮 token -> {growth}")
    print("\n读图：buffer 持续增长；window 从第 3 轮起进入平台期，成本可预测。")


if __name__ == "__main__":
    compare_backends()
