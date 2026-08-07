"""铸剑台 · s2:三路分流 —— RunnableBranch 路由器

s1 的分类链能判明来意;本步打造锻房、铭文坊两条作坊链和一间茶室,
用 RunnablePassthrough.assign + RunnableBranch 焊成自动分流的路由器:
客人一句话进来,正确的作坊接住。
"""
import os
import sys

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableBranch, RunnablePassthrough
from langchain_openai import ChatOpenAI

MOCK_LLM = os.environ.get("MOCK_LLM") == "1"

# 无 Key 且未开 MOCK 时给出引导并优雅退出
if not MOCK_LLM and not os.environ.get("OPENAI_API_KEY"):
    print("[铸剑台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

INTENT_OPTIONS = ("forge", "inscribe", "appraise", "chat")


def build_llm(mock_replies=None) -> BaseChatModel:
    """模型工厂:MOCK 时返回按剧本作答的假模型,否则接 DeepSeek。"""
    if MOCK_LLM:
        return FakeListChatModel(responses=mock_replies or ["chat"])
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0,
    )


def build_classifier_chain():
    """意图分类链(s1 的件):出口是原始判定文本。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是铸剑台的接待。判断客人来意,只回答一个词:"
                   "forge(铸剑)、inscribe(题铭文)、appraise(鉴剑)、chat(闲聊)。"),
        ("human", "{request}"),
    ])
    return prompt | build_llm(["forge", "inscribe", "appraise", "chat"]) | StrOutputParser()


def normalize_intent(raw: str) -> str:
    """清洗模型输出:包含即命中,不中归 chat。"""
    text = raw.strip().lower()
    for intent in INTENT_OPTIONS:
        if intent in text:
            return intent
    return "chat"


def build_forge_chain():
    """锻房:散文答复铸剑方案。"""
    prompt = ChatPromptTemplate.from_messages([("system", "你是铸剑大师,三句话内给出铸剑方案。"), ("human", "{request}")])
    return prompt | build_llm(["当用寒铁为骨,烈火淬之,四十九日可成。"]) | StrOutputParser()


def build_inscribe_chain():
    """铭文坊:为宝剑题铭文。"""
    prompt = ChatPromptTemplate.from_messages([("system", "你是铭文师,题一句四言或七言铭文。"), ("human", "{request}")])
    return prompt | build_llm(["霜刃未曾试,今日把示君。"]) | StrOutputParser()


def build_chat_chain():
    """茶室:闲聊兜底,也是路由器的默认分支。"""
    prompt = ChatPromptTemplate.from_messages([("system", "你是铸剑台掌柜,陪客人闲聊,谈吐风趣。"), ("human", "{request}")])
    return prompt | build_llm(["坐,炉上正温着茶,慢慢聊。"]) | StrOutputParser()


def build_router():
    """路由器:assign 先给字典追加 intent 字段,RunnableBranch 再按序分流。"""
    # 判定 + 清洗焊成一道工序:函数接在 | 后面会被自动包装成 RunnableLambda
    classify = build_classifier_chain() | normalize_intent
    return RunnablePassthrough.assign(intent=classify) | RunnableBranch(
        (lambda x: x["intent"] == "forge", build_forge_chain()),
        (lambda x: x["intent"] == "inscribe", build_inscribe_chain()),
        build_chat_chain(),  # 默认分支:其余来意(含 appraise)一律奉茶,必须存在
    )


def main() -> None:
    """四位客人轮番上门,观察分流结果。"""
    router = build_router()
    guests = ["我要铸一柄佩剑", "给此剑题句铭文", "帮我鉴赏这柄古剑", "今天天气如何"]
    print("== 铸剑台 · 三路分流 ==")
    for g in guests:
        reply = router.invoke({"request": g})
        print(f"客人:「{g}」\n  接待:{reply}")


if __name__ == "__main__":
    main()
