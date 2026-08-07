"""灵讯通 · t02-s1:消息历史
把 t01 的一次性问答升级为 ChatSession:每轮自动累积历史,模型第一次拥有"记忆"。
"""
import os
import sys
from dataclasses import dataclass

from openai import OpenAI
USE_MOCK = os.environ.get("MOCK_LLM") == "1"  # MOCK_LLM=1 时用本地假回复演示,不耗额度

# 联网前置检查:没有 Key(且未开模拟)就给出引导并优雅退出
if not USE_MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[灵讯通] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)


@dataclass
class APIConfig:
    """一次 LLM 连接所需的全部配置(见 t01-s1)。"""

    api_key: str           # 平台颁发的密钥,只从环境变量读取
    base_url: str          # OpenAI 兼容端点,决定连接哪家厂商
    model: str             # 默认调用的模型名
    timeout: float = 30.0  # 单次请求超时秒数

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
    """多轮对话会话:负责攒历史、发请求、收回复。

    LLM 是无状态的,"记忆" = 每次请求把历史消息整本重发。
    history 就是这个不断变长的剧本:user / assistant 交替追加。
    """

    def __init__(self, client: OpenAI, config: APIConfig) -> None:
        # TODO: 把 client 与 config 存到 self,并初始化 self.history 为空列表
        pass

    def _fake_reply(self, messages: list[dict]) -> str:
        """本地模拟回复:只能从 messages 里找信息,直观演示'记忆'。"""
        name = next((m["content"].split("我叫", 1)[1].strip(" 。!！?？") for m in messages
                     if m["role"] == "user" and "我叫" in m["content"]
                     and "什么" not in m["content"]), None)
        last = messages[-1]["content"]
        if "叫什么" in last or "名字" in last:
            return f"(模拟) 你叫{name}。" if name else "(模拟) 你没告诉过我名字。"
        return f"(模拟) 已收到(当前 messages 共 {len(messages)} 条)。"

    def say(self, question: str) -> str:
        """说一句:追加 user → 带全部历史发请求 → 追加 assistant。"""
        # TODO: 1) self.history.append({"role": "user", "content": question})
        #       2) 带全部历史发请求并取回复(参考):
        #          if USE_MOCK:
        #              reply = self._fake_reply(self.history)
        #          else:
        #              response = self.client.chat.completions.create(
        #                  model=self.config.model, messages=self.history, temperature=0.7)
        #              reply = response.choices[0].message.content
        #       3) reply 以 assistant 角色追加进 history,然后 return reply
        pass


def main() -> None:
    """连聊三轮:自报姓名 → 闲聊 → 反问名字,验证模型'记得'。"""
    config = APIConfig.from_env()
    session = ChatSession(create_client(config), config)

    for q in ["你好,我叫阿灵。", "我们来学多轮对话。", "考考你:我叫什么名字?"]:
        print(f"你: {q}")
        print(f"灵讯通: {session.say(q)}\n")

    print(f"会话历史共 {len(session.history)} 条消息:")
    for m in session.history:
        print(f"  [{m['role']}] {m['content'][:30]}")


if __name__ == "__main__":
    main()
