"""黑糖资料室 · 对话记忆策略 · s4：用 LangChain 完成可验证的学习任务。"""
import os
import sys
import tiktoken
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。\n请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

MOCK_REPLIES = ["幸会,阿岩!轻量海报便于移动端查看。", "移动端海报,标题会相应缩短。", "三百元以内,没问题。", "加入「山」字,好立意。", "深色边框,沉稳,配得好。"]
# MOCK 模式下摘要模型循环播放的预制摘要,模拟滚动压缩的结果
MOCK_SUMMARIES = ["客人阿岩要做一份轻方案。", "客人阿岩要做轻量海报,主要用手机,标题不宜长。", "客人阿岩要做轻量海报,预算三百元以内。", "客人阿岩要做轻量海报,预算三百元,方案加入「山」字。", "客人阿岩要做轻量海报,移动端查看,预算三百元,加入「山」字,配深色边框。"]
SCRIPT = ["我叫阿岩,想做一份轻量海报。", "我主要用手机查看,标题别太长。", "预算三百元以内。", "海报加入一个「山」字。", "搭配一个深色边框。"]

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
    """记忆后端工厂:三种策略到齐——buffer 流水账 / window 滑窗 / summary 滚动摘要。"""
    if backend == "buffer":
        return InMemoryChatMessageHistory()
    if backend == "window":
        return InMemoryChatMessageHistory()
    if backend == "summary":
        return InMemoryChatMessageHistory()
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
        growth.append(count_tokens(advisor.memory.messages))
    return growth


class ForgeAdvisor:
    """黑糖资料室接待顾问:带着一本记忆账本接待咨询者。"""

    def __init__(self, model, memory=None, backend="buffer"):
        self.model = model
        self.backend = backend
        self.memory = memory or make_memory("buffer")

    def chat(self, user_input: str) -> str:
        """一轮接待:翻账 → 连账带话发给模型 → 把问答记回账本。"""
        history = self.memory.messages
        reply = self.model.invoke([*history, HumanMessage(content=user_input)]).content
        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(reply)
        if self.backend == "window":
            self.memory.messages = self.memory.messages[-4:]
        elif self.backend == "summary":
            # 摘要是应用策略：用独立模型将旧上下文压成一条 AIMessage。
            summary = get_summary_model().invoke(
                "把以下对话压缩为不超过 80 字的事实摘要：\n" +
                "\n".join(message.content for message in self.memory.messages)
            ).content
            self.memory.messages = [AIMessage(content=summary)]
        return reply


def compare_backends(script):
    """三方对照:同剧本、同模型,唯一变量是记忆后端;summary 额外摊开摘要原文。"""
    print(f"剧本共 {len(script)} 轮,Window 后端 k=2\n")
    for backend in ("buffer", "window", "summary"):
        advisor = ForgeAdvisor(get_chat_model(MOCK_REPLIES), make_memory(backend), backend=backend)
        print(f"  后端 {backend:>7}: 逐轮 token -> {run_dialogue(advisor, script)}")
        if backend == "summary":
            # 摘要以 SystemMessage 形式留在记忆里,是模型的「背景设定」
            summary_text = advisor.memory.messages[0].content
            print(f"    摘要原文: {summary_text}")
            print(f"    「阿岩」是否幸存: {'是' if '阿岩' in summary_text else '否'}")
    print("\n读图: summary 与 window 都有平台期,但摘要保住了第 1 轮的姓名;")
    print("      代价是每轮多一次摘要 LLM 调用,且压缩有损,细节可能悄悄消失。")


def main() -> None:
    # 联网演示只需两轮即可比较三种策略，避免把同一个教学点变成 15 次 API 调用。
    # MOCK 仍保留完整五轮剧本，方便离线观察更长对话的压缩过程。
    compare_backends(SCRIPT if os.environ.get("MOCK_LLM") else SCRIPT[:2])


if __name__ == "__main__":
    main()
