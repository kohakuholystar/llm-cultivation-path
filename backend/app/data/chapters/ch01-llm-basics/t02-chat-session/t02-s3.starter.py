"""灵讯通 · t02-s3:滑动窗口
上下文不是无限的:发送时只带最近 max_turns 轮,窗口外的消息存档但不再发给模型。
"""
import os
import sys
from dataclasses import dataclass

from openai import OpenAI
USE_MOCK = os.environ.get("MOCK_LLM") == "1"  # MOCK_LLM=1 时用本地假回复演示

# 联网前置检查:没有 Key(且未开模拟)就给出引导并优雅退出
if not USE_MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[灵讯通] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

DEFAULT_PERSONA = "你是灵讯通,一个简洁可靠的命令行智能助手,回答不超过三句话。"


@dataclass
class APIConfig:
    """一次 LLM 连接所需的全部配置(见 t01-s1)。"""

    api_key: str
    base_url: str
    model: str
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "APIConfig":
        """从环境变量装配配置,缺省值指向 DeepSeek 官方端点。"""
        return cls(
            api_key=os.environ.get("OPENAI_API_KEY", "mock-key"),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
            model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
            timeout=float(os.environ.get("LLM_TIMEOUT", "30")),
        )


def create_client(config: APIConfig) -> OpenAI:
    """基于配置创建指向 DeepSeek 的客户端(见 t01-s2)。"""
    return OpenAI(api_key=config.api_key, base_url=config.base_url,
                  timeout=config.timeout, max_retries=0)


class ChatSession:
    """多轮对话会话:人设分离 + 滑动窗口截断。"""

    def __init__(self, client: OpenAI, config: APIConfig,
                 persona: str = DEFAULT_PERSONA, max_turns: int = 10) -> None:
        self.client = client
        self.config = config
        self.persona = persona
        self.history: list[dict] = []    # 完整存档:窗口外的消息也不删
        # TODO: 把 max_turns 存到 self.max_turns(一轮 = 一问一答两条消息)
        pass

    def _messages(self) -> list[dict]:
        """组装剧本:system + 最近 max_turns 轮。

        注意顺序:先切历史、再拼 system——反过来会把人设切掉。
        """
        # TODO: window = self.history[-2 * self.max_turns:]  # 成对截断,保持交替结构
        #       return [{"role": "system", "content": self.persona}, *window]
        pass

    def dropped_count(self) -> int:
        """已滑出窗口(不再发给模型)的消息条数。"""
        return max(0, len(self.history) - 2 * self.max_turns)

    def _fake_reply(self, messages: list[dict]) -> str:
        """本地模拟:只能从 messages 里找信息——窗口滑过,名字就'忘了'。"""
        name = next((m["content"].split("我叫", 1)[1].strip(" 。!！?？") for m in messages
                     if m["role"] == "user" and "我叫" in m["content"]
                     and "什么" not in m["content"]), None)
        last = messages[-1]["content"]
        if "叫什么" in last or "名字" in last:
            return f"(模拟) 你叫{name}。" if name else "(模拟) 看不到你的名字——它已滑出窗口。"
        return f"(模拟) 已收到(本轮 messages 共 {len(messages)} 条)。"

    def say(self, question: str) -> str:
        """说一句:追加 user → 带 system+窗口内历史发请求 → 追加 assistant。"""
        self.history.append({"role": "user", "content": question})
        if USE_MOCK:
            reply = self._fake_reply(self._messages())
        else:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=self._messages(),
                temperature=0.7,
            )
            reply = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": reply})
        return reply


def main() -> None:
    """max_turns=2 的会话连聊 5 轮:第 1 轮的姓名在窗口滑过后被遗忘。"""
    config = APIConfig.from_env()
    session = ChatSession(create_client(config), config, max_turns=2)

    rounds = ["你好,我叫阿灵。", "第一轮闲聊。", "第二轮闲聊。",
              "第三轮闲聊。", "考考你:我叫什么名字?"]
    for q in rounds:
        print(f"你: {q}")
        print(f"灵讯通: {session.say(q)}")
        print(f"   [窗口] 历史 {len(session.history)} 条,窗外 {session.dropped_count()} 条\n")

    print("姓名在第 1 轮,早已滑出窗口——模型'忘记'它是必然,不是 bug。")


if __name__ == "__main__":
    main()
