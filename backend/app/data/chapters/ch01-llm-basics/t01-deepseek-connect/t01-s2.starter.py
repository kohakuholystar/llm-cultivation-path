"""灵讯通 · s2:客户端封装
在 s1 配置的基础上,把"创建 OpenAI 兼容客户端"封装成可复用函数。
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


def masked_key(key: str) -> str:
    """返回打码后的 Key,日志里只露首尾 4 位。"""
    return f"{key[:4]}****{key[-4:]}"


def create_client() -> OpenAI:
    """基于全局配置创建指向 DeepSeek 的 OpenAI 兼容客户端。

    base_url 决定连哪家厂商;timeout 防止请求永久挂起;
    max_retries=0 关闭 SDK 内建重试——第 4 步我们亲手实现退避重试。
    """
    # TODO: 返回 OpenAI 客户端实例
    # 提示: OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT, max_retries=0)
    raise NotImplementedError("create_client 尚未实现:请按提示返回 OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT, max_retries=0)")


def main() -> None:
    """创建客户端、打印就绪信息。"""
    client = create_client()
    print("灵讯通客户端就绪:")
    print(f"  base_url : {BASE_URL}")
    print(f"  model    : {MODEL}")
    print(f"  api_key  : {masked_key(API_KEY)}")
    print(f"  timeout  : {TIMEOUT}s")
    print(f"  client   : {type(client).__name__}(max_retries=0)")


if __name__ == "__main__":
    main()
