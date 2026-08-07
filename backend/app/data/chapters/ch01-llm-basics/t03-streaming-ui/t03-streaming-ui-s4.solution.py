"""灵讯通 · s4:健壮流式消费封装
真实世界的流不完美:空 chunk、无文本 chunk、中途断流,safe_stream 全部兜住。
"""
import os
import sys
from dataclasses import dataclass
from types import SimpleNamespace as NS

from openai import OpenAI

MOCK = bool(os.environ.get("MOCK_LLM"))
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[灵讯通] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地演示可设置 MOCK_LLM=1,内置假流会模拟空 chunk 与断流)")
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
        return cls(
            api_key=os.environ.get("OPENAI_API_KEY", "sk-mock"),
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
            model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
            timeout=float(os.environ.get("LLM_TIMEOUT", "30")),
        )


def create_client(config: APIConfig) -> OpenAI:
    """基于配置创建指向 DeepSeek 的客户端(见 t01-s2)。"""
    return OpenAI(api_key=config.api_key, base_url=config.base_url,
                  timeout=config.timeout, max_retries=0)


@dataclass
class StreamReport:
    """流式消费的事后报告:多少有效块、跳过多少、是否断流。"""

    chunks: int = 0
    skipped: int = 0
    truncated: bool = False
    error: str = ""


def mock_stream():
    """MOCK 演示流:混入无文本 chunk 与空心跳 chunk,结尾模拟断流。"""
    for text in ["你好,", None, "", "我是灵讯通。", "正在演示"]:
        yield NS(choices=[NS(delta=NS(content=text))])  # None/空串 = 无文本块
    yield NS(choices=[])                                 # 心跳块:choices 为空
    yield NS(choices=[NS(delta=NS(content="健壮流式。"))])
    raise ConnectionError("模拟断流:连接被对端重置")      # 迭代中途抛异常


def open_stream(client: OpenAI, config: APIConfig, question: str):
    """打开流:MOCK 用内置假流,否则向 DeepSeek 发起 stream=True 请求。"""
    if MOCK:
        return mock_stream()
    return client.chat.completions.create(
        model=config.model,
        messages=[{"role": "user", "content": question}],
        stream=True,
    )


def safe_stream(client: OpenAI, config: APIConfig, question: str,
                report: StreamReport):
    """健壮流式消费生成器:跳过无效 chunk,断流时保留已收部分。

    无效 chunk 有两种:choices 为空(心跳),或 delta.content 为 None/空串
    (role 块、finish 块)。断流时生成器平静结束,调用方从 report 得知真相。
    """
    try:
        for chunk in open_stream(client, config, question):
            if not chunk.choices:        # 心跳/填充 chunk:跳过
                report.skipped += 1
                continue
            delta = chunk.choices[0].delta.content
            if not delta:                # 无文本 chunk:跳过
                report.skipped += 1
                continue
            report.chunks += 1
            yield delta
    except Exception as exc:             # 断流:已收到的部分是资产,不能丢
        report.truncated = True
        report.error = type(exc).__name__


def main() -> None:
    """打字机消费 + 事后报告:断流也能体面收场。"""
    config = APIConfig.from_env()
    client = create_client(config)
    question = "用一句话介绍你自己。"
    print(f"你: {question}")
    print("灵讯通: ", end="", flush=True)
    report = StreamReport()
    parts = list(safe_stream(client, config, question, report))
    print("".join(parts))
    if report.truncated:
        print(f"[警告] 流中途断开({report.error}),已保留收到的部分。")
    print(f"[报告] 有效块 {report.chunks},跳过无效块 {report.skipped},"
          f"断流: {'是' if report.truncated else '否'}")


if __name__ == "__main__":
    main()
