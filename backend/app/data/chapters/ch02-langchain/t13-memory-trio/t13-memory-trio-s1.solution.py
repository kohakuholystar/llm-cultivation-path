"""铸剑台 · s1:全量记忆 Buffer

铸剑台的接待顾问每天迎来送往,客人可没耐心每轮都重新自报家门。
本步给顾问装上第一本「流水账」:ConversationBufferMemory 全量记忆——
每一轮问答原样入账,下一轮连同新问题一起发给模型。
"""
import os
import sys
import warnings

from langchain_classic.memory import ConversationBufferMemory
from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# 课程环境固定用 LangChain 1.x 经典 Memory 组件做教学对照,抑制其弃用提醒以保持输出干净
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

# 联网前置检查:没 Key 且未开 MOCK 时给引导并优雅退出,不让学习者面对 traceback
if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[铸剑台] 未检测到 OPENAI_API_KEY,也未开启 MOCK_LLM 演示模式。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

MOCK_REPLIES = [
    "幸会,阿岩!轻剑省腕力,说说你的臂力和用剑习惯。",
    "你叫阿岩,想铸一柄轻剑——账上都记着呢。",
]


def get_chat_model(responses):
    """MOCK_LLM 时返回循环播放固定回复的假模型;否则返回指向 DeepSeek 的 ChatOpenAI。"""
    if os.environ.get("MOCK_LLM"):
        return FakeListChatModel(responses=responses)
    return ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
                      base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                      api_key=os.environ["OPENAI_API_KEY"], temperature=0.3)


class ForgeAdvisor:
    """铸剑台接待顾问:带着一本记忆账本接待客人。"""

    def __init__(self, model, memory=None):
        self.model = model
        # return_messages=True:账本里存消息对象列表,而不是拼好的字符串
        self.memory = memory or ConversationBufferMemory(memory_key="history", return_messages=True)

    def chat(self, user_input: str) -> str:
        """一轮接待:翻账 → 连账带话发给模型 → 把问答记回账本。"""
        history = self.memory.load_memory_variables({})["history"]
        # 历史消息排在最前、本轮输入排在最后——「记忆」就是这样被注入请求的
        reply = self.model.invoke([*history, HumanMessage(content=user_input)]).content
        # 答完立刻记账,这是显式动作,忘了下一步就失忆
        self.memory.save_context({"input": user_input}, {"output": reply})
        return reply

    def show_memory(self) -> None:
        """把账本摊开:逐条打印记忆里的消息及其类型。"""
        msgs = self.memory.chat_memory.messages
        print(f"== 记忆账本(共 {len(msgs)} 条) ==")
        for m in msgs:
            print(f"  [{type(m).__name__}] {m.content}")


def main() -> None:
    """两轮接待:第二轮考问顾问记不记得客人姓名。"""
    advisor = ForgeAdvisor(get_chat_model(MOCK_REPLIES))
    print("客人: 我叫阿岩,想铸一柄轻剑。")
    print("顾问:", advisor.chat("我叫阿岩,想铸一柄轻剑。"))
    print("客人: 我刚才说我叫什么?")
    print("顾问:", advisor.chat("我刚才说我叫什么?"))
    advisor.show_memory()


if __name__ == "__main__":
    main()
