"""黑糖资料室 · 对话记忆策略 · s1：用 LangChain 完成可验证的学习任务。"""
import os
import sys
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# 联网前置检查:没 Key 且未开 MOCK 时给引导并优雅退出,不让学习者面对 traceback
if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[提示词工作台] 未检测到 OPENAI_API_KEY,也未开启 MOCK_LLM 演示模式。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

MOCK_REPLIES = [
    "幸会,阿岩!轻量海报便于移动端查看,说说你的臂力和用方案习惯。",
    "你叫阿岩,想做一份轻量海报——账上都记着呢。",
]


def get_chat_model(responses):
    """MOCK_LLM 时返回循环播放固定回复的假模型;否则返回指向 DeepSeek 的 ChatOpenAI。"""
    if os.environ.get("MOCK_LLM"):
        return FakeListChatModel(responses=responses)
    return ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
                      base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                      api_key=os.environ["OPENAI_API_KEY"], temperature=0.3)


class ForgeAdvisor:
    """黑糖资料室接待顾问:带着一本记忆账本接待咨询者。"""

    def __init__(self, model, memory=None):
        self.model = model
        # LangChain v1 的公开消息历史：直接保存消息对象，不再使用已迁移的 Memory 类。
        self.memory = memory or InMemoryChatMessageHistory()

    def chat(self, user_input: str) -> str:
        """一轮接待:翻账 → 连账带话发给模型 → 把问答记回账本。"""
        history = self.memory.messages
        # 历史消息排在最前、本轮输入排在最后——「记忆」就是这样被注入请求的
        reply = self.model.invoke([*history, HumanMessage(content=user_input)]).content
        # 答完立刻记账,这是显式动作,忘了下一步就失忆
        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(reply)
        return reply

    def show_memory(self) -> None:
        """把账本摊开:逐条打印记忆里的消息及其类型。"""
        msgs = self.memory.messages
        print(f"== 记忆账本(共 {len(msgs)} 条) ==")
        for m in msgs:
            print(f"  [{type(m).__name__}] {m.content}")


def main() -> None:
    """两轮接待:第二轮考问顾问记不记得咨询者姓名。"""
    advisor = ForgeAdvisor(get_chat_model(MOCK_REPLIES))
    print("客人: 我叫阿岩,想做一份轻量海报。")
    print("顾问:", advisor.chat("我叫阿岩,想做一份轻量海报。"))
    print("客人: 我刚才说我叫什么?")
    print("顾问:", advisor.chat("我刚才说我叫什么?"))
    advisor.show_memory()


if __name__ == "__main__":
    main()
