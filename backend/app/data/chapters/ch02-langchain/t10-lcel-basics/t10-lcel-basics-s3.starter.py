"""黑糖资料室 · LCEL 处理管道 · s3：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：用 `prompt.partial` 为同一模板建立可复用的风格链工厂。
# - 补写：补写 `make_forge_chain` 与 `forge_one`。
# - 关键函数/类（入参 → 出参）：`make_forge_chain(style: str, llm)` 绑定风格并返回链；`forge_one(chain, material: str) -> str` 返回一次调用结果。
# - 技术栈：LangChain LCEL、`ChatPromptTemplate.partial`。
# - 前置条件：真实调用需右上角 DeepSeek API Key；风格值应来自已有 `RECIPES`。
# - 可观察结果：不同预设风格复用同一模板，得到各自结果。
import os
import sys

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")

# 黑糖资料室配方库:不同风格组 = 绑到同一模板变量上的不同预设风格
RECIPES = {
    "清新校园风": "言辞古雅,引经据典,60 字以内",
    "科幻": "用词冷峻硬核,带科技感,60 字以内",
    "校园创作": "豪情万丈,有技术社区气,60 字以内",
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
    """一座流程:全局只建一次,供所有链复用。"""
    if use_mock():
        return FakeListChatModel(responses=[
            "方案名称「晨光」,让创意被看见,今日把示君。",
            "离子锻压方案「PX-7」,充能完毕,锋值 98.2%。",
            "好方案!这份方案一出,技术社区又该热闹了。",
        ])
    return ChatOpenAI(model=MODEL_NAME, base_url=BASE_URL, temperature=0.8, timeout=30)


def make_forge_chain(style: str, llm):
    """链工厂:传入风格组名,返回一条绑好风格的专用制作链。

    prompt.partial(style=...) 把「风格」变量预先填死(类似函数柯里化),
    调用方 invoke 时只需再传 material;同一个 llm 被多条链共享。
    """
    # TODO: 1) style 不在 RECIPES 时 raise ValueError(消息带上未知风格组与可选列表);
    #       2) 用 ChatPromptTemplate.from_messages 建含 {style}/{material} 双变量的模板;
    #       3) bound = prompt.partial(style=RECIPES[style]) 绑死风格,返回 bound | llm | StrOutputParser()
    raise NotImplementedError("make_forge_chain 尚未实现:请按 TODO 提示完成校验、partial 绑定并返回管道")


def forge_one(chain, material: str) -> str:
    """单块素材制作,异常兜底不中断整流程。"""
    try:
        return chain.invoke({"material": material}).strip()
    except Exception as exc:
        return f"生成失败:{type(exc).__name__}"


def main() -> None:
    check_api_key()
    llm = build_llm()                    # 一座流程
    print(f"提示词工作台配方库开张,今日流派:{', '.join(RECIPES)}")
    for style in RECIPES:                # 三条链共用一座流程,同料不同方
        chain = make_forge_chain(style, llm)
        result = forge_one(chain, "活动素材")
        print(f"[{style}] {result}")
    print("一次处理三种输出,分别生成结果。")


if __name__ == "__main__":
    main()
