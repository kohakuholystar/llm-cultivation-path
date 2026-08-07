"""铸剑台 · s4:摘要记忆 Summary

Buffer 无损无界,Window 有负有界。摘要记忆试图两全:每轮用一个 LLM 把
「旧摘要 + 新对话」压缩成新摘要——账本厚度取决于摘要长度而非轮数,
早期关键信息也有机会在摘要里幸存。
"""
import os
import sys
import warnings

import tiktoken
from langchain_classic.memory import ConversationBufferMemory, ConversationBufferWindowMemory, ConversationSummaryMemory
from langchain_core._api.deprecation import LangChainDeprecationWarning
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# 课程固定用 LangChain 1.x 经典 Memory 组件做教学对照,抑制其弃用提醒
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[铸剑台] 未检测到 OPENAI_API_KEY。\n请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

MOCK_REPLIES = ["幸会,阿岩!轻剑省腕力。", "右手用剑,刃长会相应收短。", "三百两以内,没问题。", "刻「山」字,好立意。", "乌木剑鞘,沉稳,配得好。"]
# MOCK 模式下摘要模型循环播放的预制摘要,模拟滚动压缩的结果
MOCK_SUMMARIES = ["客人阿岩要铸一柄轻剑。", "客人阿岩要铸轻剑,惯用右手,刃不宜长。", "客人阿岩要铸轻剑,预算三百两以内。", "客人阿岩要铸轻剑,预算三百两,剑身刻「山」字。", "客人阿岩要铸轻剑,右手持剑,预算三百两,刻「山」字,配乌木鞘。"]
SCRIPT = ["我叫阿岩,想铸一柄轻剑。", "我惯用右手,剑刃别太长。", "预算三百两以内。", "剑身刻一个「山」字。", "配一个乌木剑鞘。"]

# 首次 get_encoding 会下载编码文件(之后走本地缓存);离线无缓存时退化为字符近似
try:
    ENCODING = tiktoken.get_encoding("cl100k_base")
except Exception:
    ENCODING = None


def get_chat_model(responses):
    """MOCK_LLM 时返回循环播放固定回复的假模型;否则返回指向 DeepSeek 的 ChatOpenAI。"""
    if os.environ.get("MOCK_LLM"):
        return FakeListChatModel(responses=responses)
    return ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
                      base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                      api_key=os.environ["OPENAI_API_KEY"], temperature=0.3)


def get_summary_model():
    """摘要专用模型:每轮 save_context 都会调它做一次滚动压缩,温度调低求稳。"""
    if os.environ.get("MOCK_LLM"):
        return FakeListChatModel(responses=MOCK_SUMMARIES)
    return ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
                      base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                      api_key=os.environ["OPENAI_API_KEY"], temperature=0.2)


def make_memory(backend: str):
    """记忆后端工厂:三剑客到齐——buffer 流水账 / window 滑窗 / summary 滚动摘要。"""
    if backend == "buffer":
        return ConversationBufferMemory(memory_key="history", return_messages=True)
    if backend == "window":
        return ConversationBufferWindowMemory(memory_key="history", k=2, return_messages=True)
    if backend == "summary":
        return ConversationSummaryMemory(llm=get_summary_model(), memory_key="history", return_messages=True)
    raise ValueError(f"未知记忆后端: {backend}")


def count_tokens(messages) -> int:
    """用 cl100k_base 估算一组消息的 token 数(每条 +4 结构开销);离线兜底按字符近似。"""
    if ENCODING is not None:
        return sum(len(ENCODING.encode(m.content)) + 4 for m in messages)
    return sum(len(m.content) + 4 for m in messages)


def run_dialogue(advisor, script):
    """把同一份剧本灌给顾问,返回每轮过后记忆账本的 token 数列表。"""
    growth = []
    for line in script:
        advisor.chat(line)
        growth.append(count_tokens(advisor.memory.load_memory_variables({})["history"]))
    return growth


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


def compare_backends(script):
    """三方对照:同剧本、同模型,唯一变量是记忆后端;summary 额外摊开摘要原文。"""
    print(f"剧本共 {len(script)} 轮,Window 后端 k=2\n")
    for backend in ("buffer", "window", "summary"):
        advisor = ForgeAdvisor(get_chat_model(MOCK_REPLIES), make_memory(backend))
        print(f"  后端 {backend:>7}: 逐轮 token -> {run_dialogue(advisor, script)}")
        if backend == "summary":
            # 摘要以 SystemMessage 形式留在记忆里,是模型的「背景设定」
            summary_text = advisor.memory.load_memory_variables({})["history"][0].content
            print(f"    摘要原文: {summary_text}")
            print(f"    「阿岩」是否幸存: {'是' if '阿岩' in summary_text else '否'}")
    print("\n读图: summary 与 window 都有平台期,但摘要保住了第 1 轮的姓名;")
    print("      代价是每轮多一次摘要 LLM 调用,且压缩有损,细节可能悄悄消失。")


def main() -> None:
    compare_backends(SCRIPT)


if __name__ == "__main__":
    main()
