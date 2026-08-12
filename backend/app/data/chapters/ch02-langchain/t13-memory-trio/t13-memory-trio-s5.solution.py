"""黑糖资料室 · 对话记忆策略 · s5：用 LangChain 完成可验证的学习任务。"""
import json
import os
import sys
import tiktoken
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage, messages_from_dict, messages_to_dict
from langchain_openai import ChatOpenAI

if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。\n请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

MEMORY_FILE = "forge_memory.json"
MOCK_REPLIES = ["幸会,阿岩!轻量海报便于移动端查看。", "移动端海报,标题会相应缩短。", "三百元以内,没问题。", "加入「山」字,好立意。", "深色边框,沉稳。", "下周五前交付,记下了。"]
SCRIPT = ["我叫阿岩,想做一份轻量海报。", "我主要用手机查看,标题别太长。", "预算三百元以内。", "海报加入一个「山」字。", "搭配一个深色边框。", "下周五前要交付。"]

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


def make_memory(backend: str):
    """记忆后端工厂:生产版只保留 buffer(配合上限控制),实验后端已拆除。"""
    if backend != "buffer":
        raise ValueError(f"生产版只保留 buffer 后端,收到: {backend}")
    return InMemoryChatMessageHistory()


def count_tokens(messages) -> int:
    """用 cl100k_base 估算一组消息的 token 数(每条 +4 结构开销);离线兜底按字符近似。"""
    if ENCODING is not None:
        return sum(len(ENCODING.encode(m.content)) + 4 for m in messages)
    return sum(len(m.content) + 4 for m in messages)


class ForgeAdvisor:
    def __init__(self, model, memory=None, backend="buffer"):
        self.model = model
        self.backend = backend
        self.memory = memory or make_memory(backend)

    def chat(self, user_input: str) -> str:
        """一轮接待:翻账 → 连账带话发给模型 → 把问答记回账本。"""
        history = self.memory.messages
        reply = self.model.invoke([*history, HumanMessage(content=user_input)]).content
        self.memory.add_user_message(user_input)
        self.memory.add_ai_message(reply)
        return reply

    def enforce_budget(self, max_tokens: int) -> int:
        """token 上限控制:超预算时成对淘汰最早的一问一答,返回淘汰条数。"""
        msgs = self.memory.messages
        removed = 0
        while len(msgs) > 2 and count_tokens(msgs) > max_tokens:
            del msgs[0:2]  # 成对删:孤儿消息会破坏 Human/AI 交替,有些 API 拒绝错乱序列
            removed += 2
        return removed

    def export_state(self) -> dict:
        """导出可序列化的记忆状态:messages_to_dict 给每条消息打上类型标签。"""
        return {"backend": self.backend,
                "messages": messages_to_dict(self.memory.messages)}

    def save(self, path: str = MEMORY_FILE) -> None:
        """记忆落盘:ensure_ascii=False 让中文以原文写入,账本保持人可读。"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.export_state(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, model, path: str = MEMORY_FILE) -> "ForgeAdvisor":
        """从 JSON 恢复:重建同后端记忆,把消息逐条回放进新账本。"""
        with open(path, encoding="utf-8") as f:
            state = json.load(f)
        advisor = cls(model, make_memory(state["backend"]), backend=state["backend"])
        advisor.memory.add_messages(messages_from_dict(state["messages"]))
        return advisor

    def show_memory(self) -> None:
        """把账本摊开:逐条打印记忆里的消息及其类型。"""
        msgs = self.memory.messages
        print(f"== 记忆账本(共 {len(msgs)} 条) ==")
        for m in msgs:
            print(f"  [{type(m).__name__}] {m.content}")


def main() -> None:
    """完整流程:接待 → 瘦身 → 落盘 → 模拟重启 → 恢复验证。"""
    advisor = ForgeAdvisor(get_chat_model(MOCK_REPLIES))
    for line in SCRIPT:
        advisor.chat(line)
    before = count_tokens(advisor.memory.messages)
    removed = advisor.enforce_budget(max_tokens=120)
    print(f"token 预算 120: 瘦身前 {before} → 淘汰 {removed} 条 → 现存 {count_tokens(advisor.memory.messages)}")
    advisor.save()
    print(f"\n记忆已落盘 {MEMORY_FILE}(前 120 字节):")
    with open(MEMORY_FILE, encoding="utf-8") as f:
        print(f.read(120) + " ...")
    restored = ForgeAdvisor.load(get_chat_model(MOCK_REPLIES))
    print("\n模拟重启后恢复账本:")
    restored.show_memory()


if __name__ == "__main__":
    main()
