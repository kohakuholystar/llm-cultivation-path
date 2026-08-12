"""黑糖资料室 · 对话记忆策略 · s2：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：比较完整记录与最近窗口两种对话历史策略。
# - 补写：补写记忆工厂、顾问逻辑和剧本回放。
# - 关键函数/类（入参 → 出参）：`make_memory(backend: str)` 返回指定历史后端；`fetch_real_anchor(model) -> str` 获取一次真实锚点回复；`replay_script(advisor, real_anchor) -> None` 演示历史策略。
# - 技术栈：LangChain Core、消息历史、window memory。
# - 前置条件：右上角 DeepSeek API Key 是必需项；本步只发起受控的真实调用。
# - 可观察结果：看到不同策略携带的历史范围差异。
import os
import sys

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

if not os.environ.get("OPENAI_API_KEY"):
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key，然后重新运行。")
    sys.exit(0)

SCRIPT = ["我叫阿岩，想做一份轻量海报。", "我主要用手机查看，标题别太长。", "预算三百元以内。", "海报加入一个‘山’字。"]
LOCAL_REPLIES = ["移动端海报，标题会相应缩短。", "三百元以内没有问题。", "加入‘山’字，主题会更明确。"]


def get_chat_model() -> ChatOpenAI:
    return ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"), base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"), api_key=os.environ["OPENAI_API_KEY"], temperature=0.3)


def fetch_real_anchor(model: ChatOpenAI) -> str:
    # TODO: 只调用一次 model.invoke，回应 SCRIPT[0]，并返回 .content。
    raise NotImplementedError("请实现单次真实 DeepSeek 锚点调用")


def make_memory(backend: str) -> InMemoryChatMessageHistory:
    # TODO: buffer/window 均创建 InMemoryChatMessageHistory；未知后端 raise ValueError。
    raise NotImplementedError("请实现记忆后端工厂")


class ForgeAdvisor:
    def __init__(self, memory: InMemoryChatMessageHistory, backend: str):
        self.memory = memory
        self.backend = backend

    def record_turn(self, user_input: str, reply: str) -> None:
        # TODO: 成对写入 Human/AI 消息；window 时只保留最后 4 条（k=2 轮）。
        raise NotImplementedError("请实现本地记账与窗口裁剪")

    def show_memory(self) -> None:
        for message in self.memory.messages:
            print(f"[{type(message).__name__}] {message.content}")


def replay_script(advisor: ForgeAdvisor, real_anchor: str) -> None:
    # TODO: 首轮写入 real_anchor；其余三轮用 LOCAL_REPLIES 本地回放，不可再次调用模型。
    raise NotImplementedError("请实现本地剧本回放")


def main() -> None:
    real_anchor = fetch_real_anchor(get_chat_model())
    for backend in ("buffer", "window"):
        advisor = ForgeAdvisor(make_memory(backend), backend)
        replay_script(advisor, real_anchor)
        advisor.show_memory()


if __name__ == "__main__":
    main()
