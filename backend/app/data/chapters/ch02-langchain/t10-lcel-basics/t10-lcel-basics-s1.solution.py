"""铸剑台 · 第一步:开炉点火 —— 用 ChatOpenAI 把 DeepSeek 封装成可复用的 LLM 组件。"""
import os
import sys

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_openai import ChatOpenAI

# 配置全部来自环境变量,密钥绝不写死在代码里
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")


def use_mock() -> bool:
    """MOCK_LLM=1 时进入本地演示模式:用假模型,不联网、不耗 token。"""
    return bool(os.environ.get("MOCK_LLM"))


def check_api_key() -> None:
    """真实模式下必须配置 DeepSeek Key,缺失时优雅退出而不是甩出一屏 traceback。"""
    if use_mock():
        return
    if not os.environ.get("OPENAI_API_KEY"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)


def build_llm(temperature: float = 0.7):
    """铸造 LLM 组件:两种模式返回同一接口(都有 .invoke),上层代码无感切换。"""
    if use_mock():
        # 假模型按顺序循环吐出预置回答,接口与真模型完全一致
        return FakeListChatModel(responses=[
            "青霜:剑光如霜,吹毛断发,乃陨铁之精魄所凝。",
            "寒玥:寒玉为骨,月华为锋,出鞘自带三分冷意。",
        ])
    # base_url 指向 DeepSeek 的 OpenAI 兼容端点,换供应商不改业务逻辑
    return ChatOpenAI(
        model=MODEL_NAME,
        base_url=BASE_URL,
        temperature=temperature,
        timeout=30,        # 网络异常时 30s 果断超时,不无限挂起
        max_retries=2,     # 偶发抖动自动重试两次
    )


def forge_sword_name(llm, material: str) -> str:
    """调用 LLM,为给定铸剑材料起剑名并附一句点评。"""
    prompt = f"你是一名铸剑大师。用「{material}」铸一剑,给出剑名和一句点评,60 字以内。"
    try:
        resp = llm.invoke(prompt)     # 返回的是 AIMessage 对象
        return resp.content.strip()   # 真正的文本在 .content 属性里
    except Exception as exc:          # 鉴权失败/网络超时统一兜底,不让程序崩
        return f"铸造失败:{type(exc).__name__}"


def main() -> None:
    check_api_key()
    llm = build_llm()
    mode = "本地演示(mock)" if use_mock() else "真实 API"
    print(f"炉号:{MODEL_NAME} @ {BASE_URL} [{mode}]")
    for material in ["天外陨铁", "千年寒玉"]:
        print(f"【{material}】{forge_sword_name(llm, material)}")
    print("炉火已燃,铸剑台开张。")


if __name__ == "__main__":
    main()
