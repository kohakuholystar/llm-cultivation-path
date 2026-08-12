"""黑糖资料室 · 对话记忆策略 · s3：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：比较 buffer、window、summary 对 Token 占用和上下文的影响。
# - 补写：补写记忆工厂、token 统计和对话回放。
# - 关键函数/类（入参 → 出参）：`make_memory(backend: str)` 返回策略实例；`count_tokens(messages) -> int` 返回 Token 估算；`run_dialogue(advisor, real_anchor) -> None` 记录结果。
# - 技术栈：LangChain Core、消息历史、tiktoken。
# - 前置条件：右上角 DeepSeek API Key 是必需项；摘要步骤保持受控调用次数。
# - 可观察结果：看到三种策略的历史内容与 Token 统计。
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
    # TODO: 对 SCRIPT[0] 只调用一次 model.invoke，并返回真实回复的 .content。
    raise NotImplementedError("请实现单次真实 DeepSeek 锚点调用")


def make_memory(backend: str) -> InMemoryChatMessageHistory:
    # TODO: 为 buffer/window 创建 InMemoryChatMessageHistory；未知后端 raise ValueError。
    raise NotImplementedError("请实现记忆后端工厂")


def count_tokens(messages) -> int:
    # TODO: 有 ENCODING 时按 encode 后长度 + 每条 4；否则按字符数近似。
    raise NotImplementedError("请实现 token 估算")


class ForgeAdvisor:
    def __init__(self, memory: InMemoryChatMessageHistory, backend: str):
        self.memory = memory
        self.backend = backend

    def record_turn(self, user_input: str, reply: str) -> None:
        # TODO: 写入一问一答；window 时裁剪为最近 4 条消息（k=2）。
        raise NotImplementedError("请实现本地记账与窗口裁剪")


def run_dialogue(advisor: ForgeAdvisor, real_anchor: str) -> list[int]:
    # TODO: 首轮用 real_anchor，其余用 LOCAL_REPLIES；每轮记录 count_tokens，不可再次调用模型。
    raise NotImplementedError("请实现本地剧本回放和成本记录")


def compare_backends() -> None:
    real_anchor = fetch_real_anchor(get_chat_model())
    for backend in ("buffer", "window"):
        print(backend, run_dialogue(ForgeAdvisor(make_memory(backend), backend), real_anchor))


if __name__ == "__main__":
    compare_backends()
