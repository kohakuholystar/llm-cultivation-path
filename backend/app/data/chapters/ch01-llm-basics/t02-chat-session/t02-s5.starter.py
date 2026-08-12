"""星澈助手 · t02-s5:组装完整 CLI —— REPL + 斜杠命令 + 异常隔离,正式上岗。"""
# 学习契约
# 目标：完成 t02-s5 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 1 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：create_client(config) -> OpenAI; estimate_tokens(text) -> int; repl(session) -> None; demo(session) -> None。
# 技术栈：os, sys, dataclasses, openai；前置条件：在右上角 AI 配置填入自己的 DeepSeek API Key。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
import os
import sys
from dataclasses import dataclass

from openai import OpenAI
USE_MOCK = os.environ.get("MOCK_LLM") == "1"  # MOCK_LLM=1 用本地假回复演示

if not USE_MOCK and not os.environ.get("OPENAI_API_KEY"):  # 无 Key 优雅退出
    print("[星澈助手] 未检测到 OPENAI_API_KEY。\n请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

DEFAULT_PERSONA = "你是星澈助手,一个简洁可靠的命令行智能助手,回答不超过三句话。"


@dataclass
class APIConfig:  # 连接配置(见 t01-s1):Key/端点/模型/超时
    api_key: str
    base_url: str
    model: str
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "APIConfig":
        return cls(os.environ.get("OPENAI_API_KEY", "mock-key"),
                   os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                   os.environ.get("MODEL_NAME", "deepseek-v4-pro"))


def create_client(config: APIConfig) -> OpenAI:  # 见 t01-s2
    return OpenAI(api_key=config.api_key, base_url=config.base_url, timeout=config.timeout, max_retries=0)


def estimate_tokens(text: str) -> int:
    """估算 token 数:tiktoken 精确优先,离线时退化为启发式(宁多勿少)。"""
    try:
        import tiktoken; return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except Exception:  # 离线拿不到词表:中文 1 字≈1 token,英文 4 字符≈1 token
        cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff"); return max(1, cjk + (len(text) - cjk) // 4 + 4)


class ChatSession:
    """多轮会话完全体:人设分离 + 滑动窗口 + token 预算(见 s2-s4)。"""

    def __init__(self, client: OpenAI, config: APIConfig, persona: str = DEFAULT_PERSONA,
                 max_turns: int = 10, token_budget: int = 2000) -> None:
        self.client, self.config, self.persona = client, config, persona
        self.max_turns, self.token_budget = max_turns, token_budget
        self.history: list[dict] = []

    def _messages(self) -> list[dict]:  # 组装剧本:system + 最近 max_turns 轮(成对截断)
        return [{"role": "system", "content": self.persona}, *self.history[-2 * self.max_turns:]]

    def history_tokens(self) -> int:  # system 人设 + 全部历史消息的估算 token 总量
        return estimate_tokens(self.persona) + sum(estimate_tokens(m["content"]) for m in self.history)

    def _fit_budget(self) -> int:
        """超预算时从最老一轮开始成对丢弃,返回丢弃轮数。"""
        dropped = 0
        while len(self.history) >= 2 and self.history_tokens() > self.token_budget:
            self.history = self.history[2:]; dropped += 1
        return dropped

    def _fake_reply(self, messages: list[dict]) -> str:  # 本地模拟:只能看到 messages
        name = next((m["content"].split("我叫", 1)[1].strip(" 。!！?？") for m in messages
                     if m["role"] == "user" and "我叫" in m["content"] and "什么" not in m["content"]), None)
        last = messages[-1]["content"]
        if "叫什么" in last or "名字" in last:
            return f"(模拟) 你叫{name}。" if name else "(模拟) 看不到名字,它可能在窗口外。"
        return f"(模拟) 收到(messages 共 {len(messages)} 条)。"

    def say(self, question: str) -> str:
        self.history.append({"role": "user", "content": question})
        self._fit_budget()  # 发送前先过预算闸门
        if USE_MOCK:
            reply = self._fake_reply(self._messages())
        else:
            reply = self.client.chat.completions.create(
                model=self.config.model, messages=self._messages(), temperature=0.7).choices[0].message.content
        self.history.append({"role": "assistant", "content": reply})
        return reply


def repl(session: ChatSession) -> None:
    """交互主循环:斜杠命令分流,单轮异常隔离(一轮报错不拖垮会话)。"""
    # TODO: 打印上线提示后 while True 循环:
    #   1) q = input("你: ").strip();except (EOFError, KeyboardInterrupt) 打印再见并 return;空输入 continue
    #   2) "/exit" 退出;"/reset" 清 history;"/history" 打印历史;"/tokens" 打印用量;其余走对话
    #   3) 对话:try 里 print(session.say(q)),except 打印 type(exc).__name__(单轮失败不拖垮会话)
    pass


def demo(session: ChatSession) -> None:  # 非交互演示:脚本化对话 + 用量报告(沙箱/CI 可跑)
    for q in ["你好,我叫阿灵。", "给我讲讲滑动窗口。", "考考你:我叫什么名字?"]:
        print(f"你: {q}\n星澈助手: {session.say(q)}")
    print(f"[报告] 历史 {len(session.history)} 条,约 {session.history_tokens()} tokens")


def main() -> None:
    config = APIConfig.from_env()
    session = ChatSession(create_client(config), config, max_turns=10, token_budget=2000)
    repl(session) if sys.stdin.isatty() else demo(session)  # 真人→交互;管道/沙箱→演示


if __name__ == "__main__":
    main()
