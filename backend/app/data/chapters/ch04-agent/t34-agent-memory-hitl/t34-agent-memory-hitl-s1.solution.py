"""社团工具箱 · s1:对话记忆基座
给 Agent 装上短期记忆:同一轮对话里记住用户说过的话。
"""
import os
import sys
from dataclasses import dataclass, field

from openai import OpenAI

MOCK = os.environ.get("MOCK_LLM") == "1"          # 演示模式:无网时用剧本回复
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("请先在右上角 AI 配置填入 DeepSeek API Key")
    sys.exit(0)

BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
SYSTEM_PROMPT = "你是「社团工具箱」,随身工具管家,回答简洁,并记住用户说过的信息。"


@dataclass
class ChatMemory:
    """短期对话记忆:保存最近若干轮 user/assistant 消息。"""

    max_turns: int = 10                     # 最多保留轮数,一轮 = 一问一答
    messages: list[dict] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        """写入一条消息,超出容量时从最旧的一端裁剪。"""
        self.messages.append({"role": role, "content": content})
        self.messages = self.messages[-self.max_turns * 2:]   # 只留最近 N 轮

    def history(self) -> list[dict]:
        """返回历史副本,避免调用方误改内部状态。"""
        return list(self.messages)


class LLM:
    """统一的真实/剧本 LLM 入口,方便无网环境演示。"""

    def __init__(self, client, script=None):
        self.client = client                # None 表示演示模式
        self.script = list(script or [])

    def chat(self, messages: list[dict]) -> str:
        """真实模式调 DeepSeek;剧本模式弹出下一条预设回复。"""
        if self.client is None:
            return self.script.pop(0) if self.script else "(剧本已用完)"
        resp = self.client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.3
        )
        return resp.choices[0].message.content


def build_messages(memory: ChatMemory) -> list[dict]:
    """system 提示 + 对话历史,拼成发给模型的完整 messages。"""
    return [{"role": "system", "content": SYSTEM_PROMPT}] + memory.history()


def ask(llm: LLM, memory: ChatMemory, user_input: str) -> str:
    """带记忆地问一轮:先存提问,再调模型,最后存回答。"""
    memory.add("user", user_input)
    reply = llm.chat(build_messages(memory))
    memory.add("assistant", reply)
    return reply


def main() -> None:
    client = None
    if not MOCK:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                        base_url=BASE_URL, timeout=30, max_retries=0)
    script = [                               # 演示剧本:体现"记得名字"
        "你好阿黎!我是社团工具箱,已经记住你的名字了。",
        "你叫阿黎,我们刚打过招呼。",
    ]
    llm = LLM(client, script)
    memory = ChatMemory(max_turns=10)
    for question in ["你好,我叫阿黎。", "你还记得我叫什么吗?"]:
        print(f"我: {question}")
        print(f"社团工具箱: {ask(llm, memory, question)}")
    print(f"[记忆] 保存 {len(memory.history())} 条消息,容量 {memory.max_turns} 轮")


if __name__ == "__main__":
    main()
