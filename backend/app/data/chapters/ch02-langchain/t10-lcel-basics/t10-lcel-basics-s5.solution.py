"""黑糖资料室 · LCEL 处理管道 · s5：用 LangChain 完成可验证的学习任务。"""
import os
import sys
import time

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")

# 两条路线共用同一份提示词语义,保证实验公平
SYSTEM_PROMPT = "你是内容策划助手,只输出方案名称,格式:方案名称「X」。"


def use_mock() -> bool:
    """MOCK_LLM=1 时本地演示,不联网。"""
    return bool(os.environ.get("MOCK_LLM"))


def check_api_key() -> None:
    """真实模式缺 Key 时优雅退出。"""
    if use_mock():
        return
    if not os.environ.get("OPENAI_API_KEY"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)


def call_native_sdk(material: str) -> str:
    """路线一:原生 openai SDK —— 手动拼 messages、手动剥响应,每步都自己管。"""
    if use_mock():
        return f"方案名称「{material[:2]}锋」(原生 mock)"
    from openai import OpenAI
    # 不传参:SDK 自动读 OPENAI_API_KEY / OPENAI_BASE_URL 环境变量
    client = OpenAI()
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"材料:{material}"},
        ],
    )
    # openai v1+ 返回 pydantic 对象,用属性访问,不是字典下标
    return resp.choices[0].message.content.strip()


def build_lcel_chain():
    """路线二:LCEL —— 提示词、模型、解析器各自是组件,| 一拼即成链。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "材料:{material}"),
    ])
    if use_mock():
        llm = FakeListChatModel(responses=["方案名称「晨光」(LCEL mock)"] * 3)
    else:
        llm = ChatOpenAI(model=MODEL_NAME, base_url=BASE_URL, temperature=0.7, timeout=30)
    return prompt | llm | StrOutputParser()


def compare(material: str, chain) -> None:
    """对照实验:同一输入、两条路线、各自计时,结论用数据说话。"""
    t1 = time.perf_counter()
    native = call_native_sdk(material)
    d1 = time.perf_counter() - t1
    t2 = time.perf_counter()
    lcel = chain.invoke({"material": material}).strip()
    d2 = time.perf_counter() - t2
    print(f"订单「{material}」")
    print(f"  原生 SDK: {native} ({d1:.2f}s)")
    print(f"  LCEL 链 : {lcel} ({d2:.2f}s)")


def main() -> None:
    check_api_key()
    chain = build_lcel_chain()
    print(f"提示词工作台 v0.1 对比实验 [{MODEL_NAME}]")
    for material in ["活动素材", "校园照片"]:
        compare(material, chain)
    print("结论:同处理器同火,单次调用两者相当;LCEL 胜在组件可复用、可批量、可预设,")
    print("流程长成多环链时,原生 SDK 的手动拼装会先乱。提示词工作台 v0.1 收处理器。")


if __name__ == "__main__":
    main()
