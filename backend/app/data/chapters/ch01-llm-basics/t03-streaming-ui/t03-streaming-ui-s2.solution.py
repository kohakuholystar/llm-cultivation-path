"""星澈助手 · s2:TTFT 测量
流式的第一个工程价值是可测量:首 token 延迟决定用户对"快"的感受。
"""
import os
import sys
import time
from dataclasses import dataclass

from openai import OpenAI

MOCK = bool(os.environ.get("MOCK_LLM"))
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[星澈助手] 未检测到 OPENAI_API_KEY。")
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
class StreamStats:
    """一次流式调用的计时数据。"""

    ttft_ms: float      # 首 token 延迟:从发起到第一个非空增量到达
    total_ms: float     # 总耗时:从发起到流结束
    chunk_count: int    # 非空增量块数
    char_count: int     # 累计字符数

    @property
    def chars_per_sec(self) -> float:
        """生成吞吐(字符/秒),近似观察解码速度。"""
        return self.char_count / (self.total_ms / 1000) if self.total_ms else 0.0


def iter_mock_chunks() -> list:
    """MOCK 演示:假回复切片,模拟逐块到达。"""
    reply = "TTFT 越短,用户越觉得星澈助手反应快。"
    return [reply[i:i + 2] for i in range(0, len(reply), 2)]


def stream_with_stats(client: OpenAI, config: APIConfig, question: str):
    """流式提问并测量 TTFT 与总耗时,返回 (完整回复, StreamStats)。"""
    start = time.perf_counter()          # 打点①:发起请求前
    ttft_ms = None
    parts = []
    if MOCK:
        for piece in iter_mock_chunks():
            time.sleep(0.01)             # 模拟网络逐块到达
            if ttft_ms is None:
                ttft_ms = (time.perf_counter() - start) * 1000  # 打点②:首块
            parts.append(piece)
    else:
        stream = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": question}],
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if not delta:
                continue                 # role 块/心跳块没有文本,不算首 token
            if ttft_ms is None:
                ttft_ms = (time.perf_counter() - start) * 1000  # 打点②:首块
            parts.append(delta)
    total_ms = (time.perf_counter() - start) * 1000  # 打点③:流结束
    stats = StreamStats(
        ttft_ms=ttft_ms if ttft_ms is not None else total_ms,
        total_ms=total_ms,
        chunk_count=len(parts),
        char_count=sum(len(p) for p in parts),
    )
    return "".join(parts), stats


def main() -> None:
    """跑一次流式对话并打印计时报告。"""
    config = APIConfig.from_env()
    client = create_client(config)
    question = "用两句话解释为什么首 token 延迟重要。"
    print(f"你: {question}")
    reply, stats = stream_with_stats(client, config, question)
    print(f"星澈助手: {reply}")
    print("—— 计时报告 ——")
    print(f"  TTFT(首 token 延迟): {stats.ttft_ms:.0f} ms")
    print(f"  总耗时            : {stats.total_ms:.0f} ms")
    print(f"  增量块 / 字符数   : {stats.chunk_count} / {stats.char_count}")
    print(f"  生成吞吐          : {stats.chars_per_sec:.1f} 字/秒")
    print("提示:TTFT 决定'快不快'的第一印象,总耗时决定'完没完'。")


if __name__ == "__main__":
    main()
