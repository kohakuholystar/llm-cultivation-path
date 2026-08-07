"""铸剑台 · 第二步:配方成链 —— 用 LCEL 管道 prompt | llm | parser 组装第一条锻造链。"""
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
            "剑名「断岳」,点评:重剑无锋,大巧不工。",
            "剑名「流萤」,点评:轻灵似水,剑走偏锋。",
        ])
    return ChatOpenAI(model=MODEL_NAME, base_url=BASE_URL, temperature=0.7, timeout=30)


def build_prompt() -> ChatPromptTemplate:
    """锻造配方:system 定人设与格式,human 里的 {material}/{trait} 是待填变量。"""
    # TODO: 用 ChatPromptTemplate.from_messages() 声明 system + human 两条消息
    # 提示:入参是 [(消息角色, 内容), ...];system 给铸剑师人设与字数约束,
    #       human 文案里要留出 {material} 与 {trait} 两个占位变量,并要求「命名 + 一句点评」
    raise NotImplementedError("build_prompt 尚未实现:请按 TODO 提示用 from_messages 声明模板")


def build_chain(llm):
    """LCEL 核心:三个 Runnable 用 | 串联,数据从左向右流动并自动变形。

    dict -> prompt(填模板成消息) -> llm(生成 AIMessage) -> parser(剥成纯文本 str)
    返回值仍是 Runnable,可继续 .invoke / .batch / 再拼接。
    """
    # TODO: 返回 prompt | llm | StrOutputParser() 管道
    # 提示:先 prompt = build_prompt()、parser = StrOutputParser(),再用 | 串联后 return
    raise NotImplementedError("build_chain 尚未实现:请按 TODO 提示组装管道并返回")


def forge(chain, material: str, trait: str) -> str:
    """invoke 的入参是 dict,key 必须与模板变量名一一对应,否则 KeyError。"""
    try:
        return chain.invoke({"material": material, "trait": trait}).strip()
    except Exception as exc:
        return f"铸造失败:{type(exc).__name__}"


def main() -> None:
    check_api_key()
    chain = build_chain(build_llm())   # 一条链 = 配方 + 炉火 + 出料口
    print(f"锻造链已成型:prompt | llm | parser [{MODEL_NAME}]")
    orders = [("天外陨铁", "沉重坚硬"), ("千年寒玉", "至寒至脆")]
    for material, trait in orders:
        print(f"【{material}/{trait}】{forge(chain, material, trait)}")
    print("配方成链,出炉两剑。")


if __name__ == "__main__":
    main()
