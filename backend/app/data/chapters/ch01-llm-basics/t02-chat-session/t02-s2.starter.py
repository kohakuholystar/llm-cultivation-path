"""星澈助手 · t02-s2:人设注入
system prompt 与历史分离存放,发送时现场拼装;支持 change_persona 中途换人格。
"""
# 学习契约
# 目标：完成 t02-s2 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 3 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：create_client(config) -> OpenAI; main() -> None。
# 技术栈：os, sys, dataclasses, openai；前置条件：在右上角 AI 配置填入自己的 DeepSeek API Key。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
import os
import sys
from dataclasses import dataclass

from openai import OpenAI
USE_MOCK = os.environ.get("MOCK_LLM") == "1"  # MOCK_LLM=1 时用本地假回复演示

# 联网前置检查:没有 Key(且未开模拟)就给出引导并优雅退出
if not USE_MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[星澈助手] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

# 默认人设:对语气、格式、边界的软约束
DEFAULT_PERSONA = "你是星澈助手,一个简洁可靠的命令行智能助手,回答不超过三句话。"


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
    """多轮对话会话:人设与记忆分离——system 是常量,历史是变量。"""

    def __init__(self, client: OpenAI, config: APIConfig,
                 persona: str = DEFAULT_PERSONA) -> None:
        self.client = client
        self.config = config
        self.history: list[dict] = []    # 只记 user/assistant
        # TODO: 把 persona 存到 self.persona(注意:system 不混入 history)
        pass

    def change_persona(self, persona: str) -> None:
        # TODO: 换人设:只改注入内容,历史原封不动,下一条请求立刻生效
        #       self.persona = persona
        pass

    def _messages(self) -> list[dict]:
        # TODO: 组装请求剧本:system 永远在最前,随后才是历史
        #       return [{"role": "system", "content": self.persona}, *self.history]
        pass

    def _fake_reply(self, messages: list[dict]) -> str:
        """本地模拟:回复里带上人设标签,让'换人设'肉眼可见。"""
        last = messages[-1]["content"]
        return f"(模拟·{self.persona[:10]}…) 收到:{last[:20]}(messages 共 {len(messages)} 条)"

    def say(self, question: str) -> str:
        """说一句:追加 user → 带 system+历史发请求 → 追加 assistant。"""
        self.history.append({"role": "user", "content": question})
        if USE_MOCK:
            reply = self._fake_reply(self._messages())
        else:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=self._messages(),   # system 在此现场注入
                temperature=0.7,
            )
            reply = response.choices[0].message.content
        self.history.append({"role": "assistant", "content": reply})
        return reply


def main() -> None:
    """演示:默认人设 → 中途换人设(历史不清空),语气立刻变化。"""
    config = APIConfig.from_env()
    session = ChatSession(create_client(config), config)

    print("--- 默认人设 ---")
    print(f"星澈助手: {session.say('你好,介绍一下你自己。')}")

    session.change_persona("你是一位严谨的代码评审员,先指出风险再给建议。")
    print("\n--- 换人设为代码评审员(历史不清空) ---")
    print(f"星澈助手: {session.say('int(input()) 直接用安全吗?')}")

    print(f"\n历史共 {len(session.history)} 条(注意:system 不在其中)")


if __name__ == "__main__":
    main()
