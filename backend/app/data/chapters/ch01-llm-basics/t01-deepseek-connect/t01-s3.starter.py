"""灵讯通 · s3:首次对话
构造 messages 剧本发出第一条请求,完成灵讯通的第一次真实对话。
"""
import os
import sys

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
    """基于全局配置创建指向 DeepSeek 的客户端(见 s2)。"""
    return OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=TIMEOUT,
        max_retries=0,
    )


def chat_once(client: OpenAI, question: str) -> str:
    """发送单轮提问,返回模型的回复文本。

    LLM 是无状态的:它只能看到本次请求 messages 里的内容。
    """
    # TODO: 调用 client.chat.completions.create(model=MODEL, messages=[...])
    #       注意: 参数名是 messages(复数),别写成 message,少个 s 会报错
    #       messages 含两条字典: system(人设:你是灵讯通...)与 user(内容 question)
    # TODO: 返回 response.choices[0].message.content
    raise NotImplementedError("chat_once 尚未实现:请按 TODO 提示调用 chat.completions.create 并返回 choices[0].message.content")


def main() -> None:
    """创建客户端 → 首次真实对话。"""
    client = create_client()

    question = "你好!请用一句话介绍你自己。"
    print(f"你: {question}")
    reply = chat_once(client, question)
    print(f"灵讯通: {reply}")


if __name__ == "__main__":
    main()
