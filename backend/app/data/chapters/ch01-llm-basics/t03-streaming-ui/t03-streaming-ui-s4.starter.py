"""灵讯通 · s4:健壮流式封装 —— 空 chunk 与断流都兜得住。"""
import os
import sys
from dataclasses import dataclass
from openai import OpenAI

if not os.environ.get("OPENAI_API_KEY"):
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)


@dataclass
class APIConfig:
    """连接配置(沿用 t01)。"""
    api_key: str
    base_url: str
    model: str
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "APIConfig":
        return cls(os.environ["OPENAI_API_KEY"],
                   os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                   os.environ.get("MODEL_NAME", "deepseek-v4-pro"))


def create_client(c: APIConfig) -> OpenAI:  # 同 t01-s2
    return OpenAI(api_key=c.api_key, base_url=c.base_url,
                  timeout=c.timeout, max_retries=0)


@dataclass
class StreamReport:
    """流式消费的事后报告。"""
    chunks: int = 0        # 有效文本块数
    skipped: int = 0       # 跳过的无效块数
    truncated: bool = False  # 是否中途断流
    error: str = ""        # 断流异常类型名


def safe_stream(client: OpenAI, config: APIConfig, question: str,
                report: StreamReport):
    """健壮流式消费生成器:跳过无效 chunk,断流时保留已收部分。"""
    stream = client.chat.completions.create(
        model=config.model,
        messages=[{"role": "user", "content": question}],
        stream=True,
    )
    # TODO: 用 try 包住整个 for chunk in stream 循环:
    #   1) if not chunk.choices: 心跳块,report.skipped += 1 后 continue
    #   2) delta = chunk.choices[0].delta.content,空则 skipped += 1 后 continue
    #   3) 否则 report.chunks += 1 并 yield delta
    #   except Exception as exc: report.truncated = True; report.error = 类型名
    pass


def main() -> None:
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
    print(f"[报告] 有效块 {report.chunks},跳过 {report.skipped},断流: {report.truncated}")


if __name__ == "__main__":
    main()
