"""黑糖资料室 · LCEL 处理管道 · s5：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：用同一语义提示比较原生 SDK 与 LCEL 的职责边界。
# - 补写：补写原生调用、LCEL 链和对比函数。
# - 关键函数/类（入参 → 出参）：`call_native_sdk(material: str) -> str` 直接请求 API；`build_lcel_chain()` 返回 LCEL 链；`compare(material: str, chain) -> None` 打印比较结果。
# - 技术栈：OpenAI SDK、LangChain LCEL。
# - 前置条件：真实调用需右上角 DeepSeek API Key。
# - 可观察结果：看到两条实现路径处理相同输入的结果。
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
    # TODO: 双分支:mock 直接返回假方案名;真实分支用 OpenAI() 客户端手动调 chat.completions.create
    # 提示:if use_mock(): return f"方案名「{material[:2]}锋」(原生 mock)";
    #       from openai import OpenAI;client = OpenAI();  # 不传参,自动读环境变量
    #       resp = client.chat.completions.create(model=MODEL_NAME,
    #           messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": f"素材:{material}"}]);
    #       取文本 resp.choices[0].message.content.strip()
    raise NotImplementedError("call_native_sdk 尚未实现:请按 TODO 提示完成双分支调用")


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
