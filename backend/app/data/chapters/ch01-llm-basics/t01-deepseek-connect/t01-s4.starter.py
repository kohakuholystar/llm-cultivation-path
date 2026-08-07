"""灵讯通 · s4:连接自测与重试
对话之前先探活:ping 失败按指数退避重试,把错误暴露在成本最低的时刻。
"""
import os
import sys
import time

from openai import OpenAI

# 联网前置检查:没有 Key 就给出引导并优雅退出,不让学习者面对 traceback
if not os.environ.get("OPENAI_API_KEY"):
    print("[灵讯通] 未检测到 OPENAI_API_KEY。")
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
    """基于全局配置创建指向 DeepSeek 的客户端(内建重试已关,本步自己实现)。"""
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


def health_check(client: OpenAI, retries: int = 3) -> bool:
    """连接自测:发一条成本极低的 ping,失败按指数退避重试。

    max_tokens=8:自测只要证明链路通,不为废话付费。
    """
    for attempt in range(1, retries + 1):
        try:
            # TODO: 发送 ping 探活请求:
            #   client.chat.completions.create(
            #       model=MODEL,
            #       messages=[{"role": "user", "content": "ping,请只回复 pong"}],
            #       max_tokens=8)
            raise NotImplementedError("health_check 尚未实现:请按 TODO 提示发送 ping 探活请求")
            print(f"[自测] 第 {attempt} 次尝试成功,连接正常")
            return True
        except NotImplementedError:
            raise
        except Exception as exc:  # s5 再细分错误类型,这里先笼统捕获
            # TODO: 打印失败并指数退避:time.sleep(2 ** (attempt - 1))(最后一次可不睡)
            raise NotImplementedError("health_check 的失败重试尚未实现:请按 TODO 提示打印失败并指数退避")
    print("[自测] 多次重试仍失败,请检查网络与 API Key")
    return False


def main() -> None:
    """先自测,再对话。"""
    client = create_client()

    if not health_check(client):
        sys.exit(1)  # 自测失败:非零退出码,方便脚本化判断

    question = "用一句话解释什么是大语言模型。"
    print(f"你: {question}")
    reply = chat_once(client, question)
    print(f"灵讯通: {reply}")


if __name__ == "__main__":
    main()
