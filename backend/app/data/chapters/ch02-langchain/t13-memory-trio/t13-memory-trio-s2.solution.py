"""黑糖资料室 · 对话记忆策略 · s2：用 LangChain 完成可验证的学习任务。"""
import os
import sys

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

if not os.environ.get("OPENAI_API_KEY"):
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key，然后重新运行。")
    sys.exit(0)

SCRIPT = [
    "我叫阿岩，想做一份轻量海报。",
    "我主要用手机查看，标题别太长。",
    "预算三百元以内。",
    "海报加入一个‘山’字。",
]
LOCAL_REPLIES = ["移动端海报，标题会相应缩短。", "三百元以内没有问题。", "加入‘山’字，主题会更明确。"]


def get_chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0.3,
    )


def fetch_real_anchor(model: ChatOpenAI) -> str:
    """只调用一次真实模型，作为本次演示可追溯的首轮回答。"""
    prompt = "你是内容制作顾问。用一句不超过二十字的话回应：" + SCRIPT[0]
    return model.invoke([HumanMessage(content=prompt)]).content


def make_memory(backend: str) -> InMemoryChatMessageHistory:
    if backend in {"buffer", "window"}:
        return InMemoryChatMessageHistory()
    raise ValueError(f"未知记忆后端: {backend}")


class ForgeAdvisor:
    """把一问一答记入本地账本；本步骤不在循环中重复调用模型。"""

    def __init__(self, memory: InMemoryChatMessageHistory, backend: str):
        self.memory = memory
        self.backend = backend

    def record_turn(self, user_input: str, reply: str) -> None:
        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(reply)
        if self.backend == "window":
            k = 2  # k=2 轮，即最近 4 条消息；裁剪是本地、确定性的状态变换。
            self.memory.messages = self.memory.messages[-2 * k:]

    def show_memory(self) -> None:
        print(f"== 记忆账本（共 {len(self.memory.messages)} 条）==")
        for message in self.memory.messages:
            print(f"  [{type(message).__name__}] {message.content}")


def replay_script(advisor: ForgeAdvisor, real_anchor: str) -> None:
    """首轮使用真实回答，余下三轮使用固定剧本，零额外 API 调用。"""
    advisor.record_turn(SCRIPT[0], real_anchor)
    for user_input, reply in zip(SCRIPT[1:], LOCAL_REPLIES, strict=True):
        advisor.record_turn(user_input, reply)


def main() -> None:
    real_anchor = fetch_real_anchor(get_chat_model())
    print("本次真实 DeepSeek 调用：1 次；其余三轮为本地记忆回放。")
    for backend in ("buffer", "window"):
        advisor = ForgeAdvisor(make_memory(backend), backend)
        replay_script(advisor, real_anchor)
        print(f"\n==== 后端 = {backend} ====")
        advisor.show_memory()
    print("\n对照结论：buffer 保留 8 条；window(k=2) 只保留最近 4 条。")
    print("首轮姓名‘阿岩’已被 window 挤出，说明窗口策略以可预测成本换取旧信息丢失。")


if __name__ == "__main__":
    main()
