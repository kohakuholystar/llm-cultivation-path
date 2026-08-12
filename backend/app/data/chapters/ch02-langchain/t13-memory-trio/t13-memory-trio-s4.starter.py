"""黑糖资料室 · 对话记忆策略 · s4：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：将摘要策略接入对话历史，并比较其压缩效果。
# - 补写：补写摘要模型、记忆策略和回放比较。
# - 关键函数/类（入参 → 出参）：`get_summary_model()` 返回摘要模型；`compare_backends(script) -> None` 输出策略比较；`count_tokens(messages) -> int` 统计 Token。
# - 技术栈：LangChain Core、消息摘要、tiktoken。
# - 前置条件：真实运行需右上角 DeepSeek API Key；摘要会增加一次模型调用。
# - 可观察结果：看到摘要如何用更短文本保留可用上下文。
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
    # TODO: 构造摘要专用模型:MOCK 分支放预制摘要,真实分支接 DeepSeek
    # 提示: MOCK 时 return FakeListChatModel(responses=MOCK_SUMMARIES)
    #       真实分支结构同 get_chat_model,但 temperature=0.2 求稳
    raise NotImplementedError("get_summary_model 尚未实现:请按 TODO 提示构造摘要专用模型")


def make_memory(backend: str):
    """记忆后端工厂:三种策略到齐——buffer 流水账 / window 滑窗 / summary 滚动摘要。"""
    if backend == "buffer":
        return InMemoryChatMessageHistory()
    if backend == "window":
        return InMemoryChatMessageHistory()
    # TODO: 补上 summary 分支与兜底报错
    # 提示: return InMemoryChatMessageHistory()；摘要压缩在 chat() 中显式完成。
    #       未知后端 raise ValueError(f"未知记忆后端: {backend}")
    raise NotImplementedError("make_memory 尚未实现:请按 TODO 提示补上 summary 分支与兜底报错")


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
    # TODO: 三方对照:同剧本、同模型,唯一变量是记忆后端
    # 提示: for backend in ("buffer", "window", "summary"): 建顾问跑剧本,
    #       print(f"  后端 {backend:>7}: 逐轮 token -> {run_dialogue(advisor, script)}");
    #       summary 时摊开摘要原文 history[0].content 并判断「阿岩」是否幸存;
    #       循环后打印两行读图结论
    raise NotImplementedError("compare_backends 尚未实现:请按 TODO 提示完成三方对照与摘要摊开")


def main() -> None:
    compare_backends(SCRIPT)


if __name__ == "__main__":
    main()
