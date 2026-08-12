"""星澈助手 · s6:用量与延迟观测
对话的同时采集延迟与 token 用量,给星澈助手装上第一块仪表盘。
"""
# 学习契约
# 目标：完成 t01-s6 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 3 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：create_client() -> OpenAI; friendly_error(exc) -> str; chat_with_metrics(client, question) -> 未标注; main() -> None。
# 技术栈：os, sys, time, dataclasses, openai；前置条件：在右上角 AI 配置填入自己的 DeepSeek API Key。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
import os
import sys
import time
from dataclasses import dataclass

from openai import (OpenAI, AuthenticationError, RateLimitError,
                    APITimeoutError, APIConnectionError)

# 联网前置检查:没有 Key 就给出引导并优雅退出,不让学习者面对 traceback
if not os.environ.get("OPENAI_API_KEY"):
    print("[星澈助手] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

# ---- 全局配置:从环境变量读取(字段含义见 s1) ----
API_KEY = os.environ["OPENAI_API_KEY"]
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "30"))

# 基础校验:配置有问题应在启动时就炸,而不是等请求发出去
if not API_KEY:
    raise ValueError("api_key 不能为空")
if not BASE_URL.startswith("http"):
    raise ValueError(f"base_url 非法: {BASE_URL}")
if TIMEOUT <= 0:
    raise ValueError("timeout 必须为正数")


def create_client() -> OpenAI:
    """基于全局配置创建指向 DeepSeek 的客户端。"""
    return OpenAI(api_key=API_KEY, base_url=BASE_URL,
                  timeout=TIMEOUT, max_retries=0)


def friendly_error(exc: Exception) -> str:
    """把 SDK 异常翻译成可执行的中文建议(见 s5)。"""
    if isinstance(exc, AuthenticationError):
        return "认证失败(401):API Key 无效或已过期,请检查右上角 AI 配置。"
    if isinstance(exc, RateLimitError):
        return "触发限流(429):请求过频或余额不足,请稍后重试。"
    if isinstance(exc, APITimeoutError):  # 注意:须在 APIConnectionError 之前判断
        return "请求超时:网络不佳或服务繁忙,可调大 LLM_TIMEOUT 后重试。"
    if isinstance(exc, APIConnectionError):
        return "连接失败:请检查网络、代理与 base_url 配置。"
    return f"调用出错: {type(exc).__name__}: {exc}"


@dataclass
class CallMetrics:
    """一次调用的观测数据:延迟 + token 账单明细。"""

    # TODO: 声明四个字段: latency_ms: float、prompt_tokens: int、
    #       completion_tokens: int、total_tokens: int
    pass


def chat_with_metrics(client: OpenAI, question: str):
    """发送提问并采集延迟与用量;失败时打印友好提示并返回 None。"""
    # TODO: 1) start = time.perf_counter()
    #       2) try 调 client.chat.completions.create(model=MODEL, messages=[...])
    #          except 时 print(friendly_error(exc)) 并 return None
    #       3) latency_ms = (time.perf_counter() - start) * 1000
    #       4) 从 response.usage 取 prompt/completion/total tokens 装入 CallMetrics
    #       5) return response.choices[0].message.content, CallMetrics(...)
    raise NotImplementedError("chat_with_metrics 尚未实现:请按 TODO 提示采集延迟与用量并返回 (回复, CallMetrics)")


def main() -> None:
    """带观测的对话 → 打印调用报告。"""
    client = create_client()

    result = chat_with_metrics(client, "用一句话介绍 DeepSeek。")
    if result is None:
        sys.exit(1)
    reply, m = result

    print(f"星澈助手: {reply}")
    print("--- 调用报告 ---")
    print(f"延迟      : {m.latency_ms:.0f} ms")
    print(f"输入 token: {m.prompt_tokens}")
    print(f"输出 token: {m.completion_tokens}")
    print(f"生成速度  : {m.completion_tokens / (m.latency_ms / 1000):.1f} tokens/s")


if __name__ == "__main__":
    main()
