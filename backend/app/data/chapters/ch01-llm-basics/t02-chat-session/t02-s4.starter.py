"""灵讯通 · t02-s4:token 预算 —— 发送前过预算闸门,从最老一轮开始丢。"""
import os
import sys
from dataclasses import dataclass

from openai import OpenAI
USE_MOCK = os.environ.get("MOCK_LLM") == "1"  # MOCK_LLM=1 时用本地假回复演示

# 联网前置检查:没有 Key(且未开模拟)就给出引导并优雅退出
if not USE_MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[灵讯通] 未检测到 OPENAI_API_KEY。\n请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

DEFAULT_PERSONA = "你是灵讯通,一个简洁可靠的命令行智能助手,回答不超过三句话。"


@dataclass
class APIConfig:  # 连接配置,见 t01-s1
    api_key: str
    base_url: str
    model: str
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "APIConfig":
        return cls(  # 缺省值指向 DeepSeek 官方端点
            api_key=os.environ.get("OPENAI_API_KEY", "mock-key"),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
            model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
            timeout=float(os.environ.get("LLM_TIMEOUT", "30")),
        )


def create_client(config: APIConfig) -> OpenAI:
    return OpenAI(api_key=config.api_key, base_url=config.base_url,  # 见 t01-s2
                  timeout=config.timeout, max_retries=0)


def estimate_tokens(text: str) -> int:
    """估算 token 数:tiktoken 精确优先,离线时退化为启发式(宁多勿少)。"""
    # TODO: try: import tiktoken;return len(tiktoken.get_encoding("cl100k_base").encode(text))
    #       except Exception: cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff");返回 max(1, cjk + (len(text) - cjk) // 4 + 4)
    pass


class ChatSession:
    """多轮对话会话:人设分离 + 滑动窗口 + token 预算闸门。"""

    def __init__(self, client: OpenAI, config: APIConfig,
                 persona: str = DEFAULT_PERSONA,
                 max_turns: int = 10, token_budget: int = 2000) -> None:
        self.client = client
        self.config = config
        self.persona = persona
        self.max_turns = max_turns
        self.token_budget = token_budget  # 历史 token 上限(含 system 人设)
        self.history: list[dict] = []

    def _messages(self) -> list[dict]:  # 组装剧本:system + 最近 max_turns 轮(见 s3)
        window = self.history[-2 * self.max_turns:]
        return [{"role": "system", "content": self.persona}, *window]

    def history_tokens(self) -> int:  # system 人设 + 全部历史消息的估算 token 总量
        # TODO: return estimate_tokens(self.persona) + sum(
        #            estimate_tokens(m["content"]) for m in self.history)
        pass

    def _fit_budget(self) -> int:
        """超预算时从最老的一轮开始成对丢弃,返回丢弃轮数。"""
        # TODO: dropped = 0
        #       while len(self.history) >= 2 and self.history_tokens() > self.token_budget:
        #           self.history = self.history[2:]  # 成对丢弃,保持 user/assistant 交替
        #           dropped += 1
        #       循环结束后 return dropped
        pass

    def _fake_reply(self, messages: list[dict]) -> str:
        """本地模拟:只能从 messages 里找信息,预算丢弃后同样会'遗忘'。"""
        name = next((m["content"].split("我叫", 1)[1].strip(" 。!！?？") for m in messages
                     if m["role"] == "user" and "我叫" in m["content"]
                     and "什么" not in m["content"]), None)
        last = messages[-1]["content"]
        if "叫什么" in last or "名字" in last:
            return f"(模拟) 你叫{name}。" if name else "(模拟) 看不到名字——它被预算闸门丢弃了。"
        return f"(模拟) 已收到(本轮 messages 共 {len(messages)} 条)。"

    def say(self, question: str) -> str:
        """说一句:追加 → 过预算闸门 → 发请求 → 收回复。"""
        self.history.append({"role": "user", "content": question})
        dropped = self._fit_budget()  # 发送前先过预算闸门
        if dropped:
            print(f"   [预算] 超出 {self.token_budget} tokens,已丢弃最老的 {dropped} 轮")
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
    """token_budget=80 的小预算会话:长消息迅速挤掉最早的轮次。"""
    config = APIConfig.from_env()
    session = ChatSession(create_client(config), config, token_budget=80)

    rounds = ["你好,我叫阿灵,正在学习上下文管理。", "请详细解释大模型为什么要限制上下文长度。",
              "再讲讲滑动窗口和摘要压缩各有什么优缺点。", "考考你:我叫什么名字?"]
    for q in rounds:
        print(f"你: {q}")
        print(f"灵讯通: {session.say(q)}")
        print(f"   [预算] 当前历史约 {session.history_tokens()} / {session.token_budget} tokens\n")


if __name__ == "__main__":
    main()
