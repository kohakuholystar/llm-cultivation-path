"""铸剑台 · s2:滑动窗口 Window

Buffer 的账本无限变厚,Window 只保留最近 k 轮:token 开销有了上限,
代价是被挤出窗口的旧信息对模型而言从未存在过。本步用同一份剧本做对照。
"""
import os
import sys
import warnings

from langchain_classic.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[铸剑台] 未检测到 OPENAI_API_KEY,也未开启 MOCK_LLM 演示模式。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

MOCK_REPLIES = [
    "幸会,阿岩!轻剑省腕力。",
    "右手用剑,记下了,刃长会相应收短。",
    "三百两以内,没问题。",
    "刻「山」字,好立意。",
]

SCRIPT = [
    "我叫阿岩,想铸一柄轻剑。",
    "我惯用右手,剑刃别太长。",
    "预算三百两以内。",
    "剑身刻一个「山」字。",
]


def get_chat_model(responses):
    """MOCK_LLM 时返回循环播放固定回复的假模型;否则返回指向 DeepSeek 的 ChatOpenAI。"""
    if os.environ.get("MOCK_LLM"):
        return FakeListChatModel(responses=responses)
    return ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
                      base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                      api_key=os.environ["OPENAI_API_KEY"], temperature=0.3)


def make_memory(backend: str):
    """记忆后端工厂:字符串切换,保证对照实验里只有后端这一个变量。"""
    if backend == "buffer":
        return ConversationBufferMemory(memory_key="history", return_messages=True)
    # TODO: 补上 window 分支与兜底报错
    # 提示: ConversationBufferWindowMemory(memory_key="history", k=2, return_messages=True)
    #       k 的单位是「轮」不是「条」:k=2 保留最近 2 轮 = 4 条消息
    #       未知后端 raise ValueError(f"未知记忆后端: {backend}")
    raise NotImplementedError("make_memory 尚未实现:请按 TODO 提示补上 window 分支与兜底报错")


class ForgeAdvisor:
    """铸剑台接待顾问:带着一本记忆账本接待客人。"""

    def __init__(self, model, memory=None):
        self.model = model
        self.memory = memory or make_memory("buffer")

    def chat(self, user_input: str) -> str:
        """一轮接待:翻账 → 连账带话发给模型 → 把问答记回账本。"""
        history = self.memory.load_memory_variables({})["history"]
        reply = self.model.invoke([*history, HumanMessage(content=user_input)]).content
        self.memory.save_context({"input": user_input}, {"output": reply})
        return reply

    def show_memory(self) -> None:
        """把账本摊开:逐条打印记忆里的消息及其类型。"""
        msgs = self.memory.chat_memory.messages
        print(f"== 记忆账本(共 {len(msgs)} 条) ==")
        for m in msgs:
            print(f"  [{type(m).__name__}] {m.content}")


def main() -> None:
    """同一份四轮剧本喂给两种后端,摊开账本对照挤出效应。"""
    # TODO: 用同一份剧本喂给两种后端,摊开账本对照挤出效应
    # 提示: for backend in ("buffer", "window"):
    #       建顾问 → 逐行跑 SCRIPT → print(f"\n==== 后端 = {backend} ====") → advisor.show_memory()
    #       循环结束后打印两行对照结论(buffer 八条全在,window 只留最近两轮)
    raise NotImplementedError("main 尚未实现:请按 TODO 提示完成双后端对照并打印结论")


if __name__ == "__main__":
    main()
