"""星澈助手 · s5:错误分类处理
按"对策"给错误分类:401 查 Key、429 退避重试、超时/断连查网络。
"""
# 学习契约
# 目标：完成 t01-s5 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 12 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：create_client() -> OpenAI; chat_once(client, question) -> str; friendly_error(exc) -> str; chat_safely(client, question) -> 未标注。
# 技术栈：os, sys, time, openai；前置条件：在右上角 AI 配置填入自己的 DeepSeek API Key。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
import os
import sys
import time

# SDK 异常速查:AuthenticationError=401 Key 无效;RateLimitError=429 限流;
# APITimeoutError 是 APIConnectionError 的子类(判断顺序不能反)
from openai import (OpenAI, AuthenticationError, RateLimitError,
                    APITimeoutError, APIConnectionError)

# 联网前置检查:没有 Key 就给出引导并优雅退出,不让学习者面对 traceback
if not os.environ.get("OPENAI_API_KEY"):
    print("[星澈助手] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

# 值得退避重试的错误:限流、超时、断连(401 重试无意义)
RETRYABLE_ERRORS = (RateLimitError, APITimeoutError, APIConnectionError)

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
    return OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=TIMEOUT,
        max_retries=0,
    )


def chat_once(client: OpenAI, question: str) -> str:
    """发送单轮提问,返回回复文本(见 s3)。"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": question}],
        temperature=0.7,
    )
    return response.choices[0].message.content


def friendly_error(exc: Exception) -> str:
    """把 SDK 异常翻译成可执行的中文建议(给用户对策,不给堆栈)。"""
    # TODO: isinstance 逐类判断并返回中文建议(APITimeoutError 须在 APIConnectionError 之前):
    #   AuthenticationError→认证失败(401) RateLimitError→限流(429) 超时→请求超时 断连→连接失败
    raise NotImplementedError("friendly_error 尚未实现:请按 TODO 提示用 isinstance 逐类判断并返回中文建议")


def chat_safely(client: OpenAI, question: str):
    """调 chat_once;异常时打印友好提示并返回 None,不让 traceback 糊用户一脸。"""
    # TODO: try 返回 chat_once(...);except 时 print(friendly_error(exc)) 并 return None
    raise NotImplementedError("chat_safely 尚未实现:请按 TODO 提示用 try/except 包装 chat_once 并打印友好提示")


def health_check(client: OpenAI, retries: int = 3) -> bool:
    """ping 探活:只对可重试错误指数退避,其余错误(如 401)立即放弃。"""
    for attempt in range(1, retries + 1):
        try:
            client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": "ping,请只回复 pong"}],
                max_tokens=8,
            )
            print(f"[自测] 第 {attempt} 次尝试成功,连接正常")
            return True
        except RETRYABLE_ERRORS as exc:
            wait = 2 ** (attempt - 1)  # 指数退避:1s → 2s → 4s
            print(f"[自测] 第 {attempt} 次失败({type(exc).__name__}),{wait}s 后重试")
            if attempt < retries:
                time.sleep(wait)
        except Exception as exc:
            # TODO: 打印 friendly_error(exc) 并 return False(不可重试错误直接放弃)
            raise NotImplementedError("health_check 的失败处理尚未实现:请按 TODO 提示分类处理并退避")
    print("[自测] 多次重试仍失败")
    return False


def fault_bad_key(question: str) -> None:
    """故障注入①:Key 末尾加 x,应触发认证失败(401)。"""
    # TODO: 构造坏 Key 客户端:api_key=API_KEY + "x"(全局变量 + 故障注入),
    #       其余参数照抄 create_client;再调 chat_safely(bad_client, question)
    raise NotImplementedError("fault_bad_key 尚未实现:请按 TODO 提示构造坏 Key 客户端并调用 chat_safely")


def fault_bad_url(question: str) -> None:
    """故障注入②:域名末尾加 x,应触发连接失败。"""
    # TODO: 构造坏域名客户端:base_url=BASE_URL + "x"(全局变量 + 故障注入),
    #       其余参数照抄 create_client;再调 chat_safely(bad_client, question)
    raise NotImplementedError("fault_bad_url 尚未实现:请按 TODO 提示构造坏域名客户端并调用 chat_safely")


def fault_tiny_timeout(question: str) -> None:
    """故障注入③:超时压到毫秒级,应触发请求超时。"""
    # TODO: 构造极小超时客户端:timeout=TIMEOUT / 3000(全局变量 + 故障注入),
    #       其余参数照抄 create_client;再调 chat_safely(bad_client, question)
    raise NotImplementedError("fault_tiny_timeout 尚未实现:请按 TODO 提示构造极小超时客户端并调用 chat_safely")


def main() -> None:
    """自测(智能重试)→ 故障注入(让错误处理现出原形)。"""
    client = create_client()

    if not health_check(client):
        sys.exit(1)

    question = "用一句话解释什么是大语言模型。"

    print("\n=== 故障注入验证:故意制造三类错误,看 friendly_error 是否各归其位 ===")
    print("[故障①] Key 末尾加 x → 应提示:认证失败(401)")
    fault_bad_key(question)
    print("[故障②] 域名末尾加 x → 应提示:连接失败")
    fault_bad_url(question)
    print("[故障③] 超时压到毫秒级 → 应提示:请求超时")
    fault_tiny_timeout(question)


if __name__ == "__main__":
    main()
