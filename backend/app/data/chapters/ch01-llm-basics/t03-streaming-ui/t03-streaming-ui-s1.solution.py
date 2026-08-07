"""灵讯通 · s1:流式初体验
stream=True 把一次性响应变成一连串增量 chunk,拼接即得完整回复。
"""
import os
import sys
from dataclasses import dataclass

from openai import OpenAI

# 联网前置检查:无 Key 且未开 MOCK 演示模式时,给出引导并优雅退出
MOCK = bool(os.environ.get("MOCK_LLM"))
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[灵讯通] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地演示可设置 MOCK_LLM=1 使用内置假回复)")
    sys.exit(0)


@dataclass
class APIConfig:
    """一次 LLM 连接所需的全部配置(沿用 t01-s1)。"""

    api_key: str
    base_url: str
    model: str
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "APIConfig":
        """从环境变量装配配置,缺省值指向 DeepSeek 官方端点。"""
        return cls(
            api_key=os.environ.get("OPENAI_API_KEY", "sk-mock"),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
            model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
            timeout=float(os.environ.get("LLM_TIMEOUT", "30")),
        )


def create_client(config: APIConfig) -> OpenAI:
    """基于配置创建指向 DeepSeek 的客户端(见 t01-s2)。"""
    return OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=config.timeout,
        max_retries=0,
    )


def iter_mock_chunks() -> list:
    """MOCK 演示:把一句假回复切成两字一片的增量序列。"""
    reply = "流式输出让灵讯通边想边说,等待变成了阅读。"
    return [reply[i:i + 2] for i in range(0, len(reply), 2)]


def stream_chat(client: OpenAI, config: APIConfig, question: str):
    """流式发送提问,逐块收集增量文本,返回 (完整回复, 块数)。"""
    if MOCK:
        chunks = iter_mock_chunks()  # 本地演示:不联网也能看到增量效果
    else:
        stream = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": question}],
            stream=True,  # 关键开关:服务端边生成边推送(SSE)
        )
        chunks = []
        for chunk in stream:
            # 流式文本在 delta.content(增量),不是 message.content(全量)
            delta = chunk.choices[0].delta.content
            if delta:  # role 块/结束块的 content 为 None,必须判空
                chunks.append(delta)
    return "".join(chunks), len(chunks)


def main() -> None:
    """配置 → 客户端 → 第一次流式对话。"""
    config = APIConfig.from_env()
    client = create_client(config)
    question = "用一句话夸夸流式输出。"
    print(f"你: {question}")
    reply, n = stream_chat(client, config, question)
    print(f"灵讯通: {reply}")
    print(f"[统计] 共收到 {n} 个增量块,拼接后 {len(reply)} 字")
    print("提示:每个块只有几个字,完整回复是拼出来的。")


if __name__ == "__main__":
    main()
