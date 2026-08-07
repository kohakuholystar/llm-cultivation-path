"""铸剑台 · 第四步:批量开炉 —— chain.batch 并发锻造与串行 invoke 的对比实验。"""
import os
import sys
import time

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")

# 今日订单:六块材料,逐一命名
ORDERS = ["天外陨铁", "千年寒玉", "深海玄铜", "雷击桃木", "昆仑冰晶", "大漠金沙"]


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


def build_llm():
    if use_mock():
        # 假模型回答循环使用,六份订单正好轮一轮
        return FakeListChatModel(responses=[
            "剑名「青霜」", "剑名「寒玥」", "剑名「玄鲸」",
            "剑名「惊雷」", "剑名「凝冰」", "剑名「流砂」",
        ])
    return ChatOpenAI(model=MODEL_NAME, base_url=BASE_URL, temperature=0.7, timeout=30)


def build_chain(llm):
    """只输出剑名的极简配方,便于对齐对比。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是铸剑师,只输出剑名,格式:剑名「X」。"),
        ("human", "材料:{material}"),
    ])
    return prompt | llm | StrOutputParser()


def forge_sequential(chain, orders: list) -> list:
    """串行:一把接一把,总耗时 ≈ 单次耗时 × N。"""
    results = []
    for material in orders:
        results.append(chain.invoke({"material": material}))
    return results


def forge_batch(chain, orders: list, workers: int = 3) -> list:
    """并发:batch 内部开线程池同时发请求,结果列表与输入保序一一对应。"""
    # TODO: 把订单转成 dict 列表,再用 chain.batch 并发调用
    # 提示:inputs = [{"material": m} for m in orders];
    #       return chain.batch(inputs, config={"max_concurrency": workers})
    raise NotImplementedError("forge_batch 尚未实现:请按 TODO 提示转 dict 列表并调用 chain.batch")


def timed(fn, *args):
    """计时小工具:返回 (耗时秒, 结果),让对比有数据而非感觉。"""
    start = time.perf_counter()
    result = fn(*args)
    return time.perf_counter() - start, result


def main() -> None:
    check_api_key()
    chain = build_chain(build_llm())
    print(f"今日订单 {len(ORDERS)} 份,开炉 [{MODEL_NAME}]")
    t1, seq = timed(forge_sequential, chain, ORDERS)
    t2, bat = timed(forge_batch, chain, ORDERS)
    assert len(seq) == len(bat) == len(ORDERS), "批量与串行结果数量必须一致"
    for material, name in zip(ORDERS, bat):      # batch 保序,放心 zip
        print(f"【{material}】{name.strip()}")
    print(f"串行耗时 {t1:.2f}s / 批量耗时 {t2:.2f}s")
    print("批量开炉,效率立现。")


if __name__ == "__main__":
    main()
