"""铸剑台 · 第三步:一炉多铸 —— 链工厂 + prompt.partial 预设配方库。"""
import os
import sys

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")

# 铸剑台配方库:不同流派 = 绑到同一模板变量上的不同预设风格
RECIPES = {
    "古风": "言辞古雅,引经据典,60 字以内",
    "科幻": "用词冷峻硬核,带科技感,60 字以内",
    "武侠": "豪情万丈,有江湖气,60 字以内",
}


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
    """一座炉:全局只建一次,供所有链复用。"""
    if use_mock():
        return FakeListChatModel(responses=[
            "剑名「青霜」,霜刃未曾试,今日把示君。",
            "离子锻压剑「PX-7」,充能完毕,锋值 98.2%。",
            "好剑!此剑一出,江湖又该热闹了。",
        ])
    return ChatOpenAI(model=MODEL_NAME, base_url=BASE_URL, temperature=0.8, timeout=30)


def make_forge_chain(style: str, llm):
    """链工厂:传入流派名,返回一条绑好风格的专用锻造链。

    prompt.partial(style=...) 把「风格」变量预先填死(类似函数柯里化),
    调用方 invoke 时只需再传 material;同一个 llm 被多条链共享。
    """
    if style not in RECIPES:
        raise ValueError(f"未知流派:{style},可选:{list(RECIPES)}")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是铸剑台首席铸剑师,风格要求:{style}"),
        ("human", "用「{material}」铸一剑,给出剑名和一句点评。"),
    ])
    # 注意:partial 返回新模板,必须接住返回值,单写一行等于没绑
    bound = prompt.partial(style=RECIPES[style])
    return bound | llm | StrOutputParser()


def forge_one(chain, material: str) -> str:
    """单块材料锻造,异常兜底不中断整炉。"""
    try:
        return chain.invoke({"material": material}).strip()
    except Exception as exc:
        return f"铸造失败:{type(exc).__name__}"


def main() -> None:
    check_api_key()
    llm = build_llm()                    # 一座炉
    print(f"铸剑台配方库开张,今日流派:{', '.join(RECIPES)}")
    for style in RECIPES:                # 三条链共用一座炉,同料不同方
        chain = make_forge_chain(style, llm)
        result = forge_one(chain, "天外陨铁")
        print(f"[{style}] {result}")
    print("一炉三铸,各成其剑。")


if __name__ == "__main__":
    main()
