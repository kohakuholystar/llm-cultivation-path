"""铸剑台 · s4:备好退路 —— with_fallbacks 降级链

结构化锻房有一个软肋:模型输出不合契约时 parser 会抛异常,链条当场崩断。
本步给锻房挂上"备用炉":primary.with_fallbacks([fallback]),
主链失败自动切散文副链,客人绝不空手而归;
MOCK 剧本里第一炉 JSON 残缺逼出降级,第二炉合格展示恢复。
"""
import os
import sys

from pydantic import BaseModel, Field
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
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
MOCK_SWORD_JSON = '{"name": "青霜", "material": "寒铁", "sharpness": 92, "inscription": "霜刃未曾试"}'


class SwordOrder(BaseModel):
    """铸剑单(t12 的数据契约):锻房的硬出口。"""

    name: str = Field(description="剑名,两到四个汉字")
    material: str = Field(description="主材,如 寒铁/玄钢/陨星砂")
    sharpness: int = Field(ge=1, le=100, description="锋芒值,1-100")
    inscription: str = Field(description="剑身铭文,不超过十二字")


parser = PydanticOutputParser(pydantic_object=SwordOrder)


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
    """意图分类链:本步剧本判出 铸剑 → 铭文 → 铸剑。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是铸剑台的接待。判断客人来意,只回答一个词:"
                   "forge(铸剑)、inscribe(题铭文)、appraise(鉴剑)、chat(闲聊)。"),
        ("human", "{request}"),
    ])
    return prompt | build_llm(["forge", "inscribe", "forge"]) | StrOutputParser()


def normalize_intent(raw: str) -> str:
    text = raw.strip().lower()
    for intent in INTENT_OPTIONS:
        if intent in text:
            return intent
    return "chat"


def build_structured_forge_chain():
    """锻房主链:产出 SwordOrder;JSON 不合格会抛 OutputParserException。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是铸剑大师,按契约输出铸剑单 JSON。"),
        ("human", "客人需求:{request}\n{format_instructions}"),
    ]).partial(format_instructions=parser.get_format_instructions())
    # MOCK 剧本:第一炉 JSON 残缺(逼出降级),第二炉合格(展示恢复)
    return prompt | build_llm(['{"name": "青霜", "material": "寒铁", "sha', MOCK_SWORD_JSON]) | parser


def build_fallback_forge_chain():
    """锻房副链:不要契约只要人话,故障面更小,兜底用。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是铸剑大师,用三句散文给出铸剑建议。"),
        ("human", "{request}"),  # 输入变量必须与主链一致,否则降级时再炸一次
    ])
    return prompt | build_llm(["[降级] 炉火正旺,且以玄钢打底,徐徐图之。"]) | StrOutputParser()


def build_forge_chain():
    """主链挂副链:主链抛异常时自动降级,客人绝不空手而归。"""
    # with_fallbacks 的参数是 Runnable 的【列表】,按序尝试;默认捕获所有 Exception
    return build_structured_forge_chain().with_fallbacks([build_fallback_forge_chain()])


def build_inscribe_chain():
    """铭文坊:为宝剑题铭文。"""
    prompt = ChatPromptTemplate.from_messages([("system", "你是铭文师,题一句四言或七言铭文。"), ("human", "{request}")])
    return prompt | build_llm(["霜刃未曾试,今日把示君。"]) | StrOutputParser()


def build_router():
    """路由器照旧:挂了降级的锻房链对上游完全透明。"""
    classify = build_classifier_chain() | normalize_intent
    return RunnablePassthrough.assign(intent=classify) | RunnableBranch(
        (lambda x: x["intent"] == "forge", build_forge_chain()),
        (lambda x: x["intent"] == "inscribe", build_inscribe_chain()),
        build_inscribe_chain(),  # 默认分支
    )


def main() -> None:
    """两次铸剑:第一炉降级为散文,第二炉恢复正常出铸剑单。"""
    router = build_router()
    guests = ["我要铸一柄佩剑", "给此剑题句铭文", "再铸一柄更好的"]
    print("== 铸剑台 · 备用炉演练 ==")
    for g in guests:
        result = router.invoke({"request": g})
        if isinstance(result, SwordOrder):
            print(f"「{g}」→ 主链出货 · 铸剑单:{result.name}|锋芒{result.sharpness}")
        else:  # 副链散文自带 [降级] 标记:主链失手,备用炉顶上
            print(f"「{g}」→ {result}")


if __name__ == "__main__":
    main()
