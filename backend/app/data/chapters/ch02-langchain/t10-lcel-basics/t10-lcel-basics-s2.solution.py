"""黑糖资料室 · LCEL 处理管道 · s2：用 LangChain 完成可验证的学习任务。"""
import os
import sys

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")


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
    """模型组件:mock 与真实两种实现,接口一致。"""
    if use_mock():
        return FakeListChatModel(responses=[
            "方案名称「断岳」,点评:长篇方案无锋,大巧不工。",
            "方案名称「流萤」,点评:轻灵似水,方案走偏锋。",
        ])
    return ChatOpenAI(model=MODEL_NAME, base_url=BASE_URL, temperature=0.7, timeout=30)


def build_prompt() -> ChatPromptTemplate:
    """制作配方:system 定人设与格式,human 里的 {material}/{trait} 是待填变量。"""
    return ChatPromptTemplate.from_messages([
        ("system", "你是提示词工作台首席内容策划助手,言辞古雅精炼,每次回答不超过 60 字。"),
        ("human", "材料:{material}\n特性:{trait}\n请为这份方案命名并附一句点评,格式:方案名称「X」,点评:..."),
    ])


def build_chain(llm):
    """LCEL 核心:三个 Runnable 用 | 串联,数据从左向右流动并自动变形。

    dict -> prompt(填模板成消息) -> llm(生成 AIMessage) -> parser(剥成纯文本 str)
    返回值仍是 Runnable,可继续 .invoke / .batch / 再拼接。
    """
    prompt = build_prompt()
    parser = StrOutputParser()
    return prompt | llm | parser


def forge(chain, material: str, trait: str) -> str:
    """invoke 的入参是 dict,key 必须与模板变量名一一对应,否则 KeyError。"""
    try:
        return chain.invoke({"material": material, "trait": trait}).strip()
    except Exception as exc:
        return f"生成失败:{type(exc).__name__}"


def main() -> None:
    check_api_key()
    chain = build_chain(build_llm())   # 一条链 = 配方 + 流程火 + 出料口
    print(f"内容生成链已成型:prompt | llm | parser [{MODEL_NAME}]")
    orders = [("活动素材", "沉重坚硬"), ("校园照片", "色调清冷")]
    for material, trait in orders:
        print(f"【{material}/{trait}】{forge(chain, material, trait)}")
    print("配方成链,输出运行两方案。")


if __name__ == "__main__":
    main()
