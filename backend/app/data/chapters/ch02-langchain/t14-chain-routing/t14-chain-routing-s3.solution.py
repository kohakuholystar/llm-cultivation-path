"""铸剑台 · s3:锻房升级 —— 结构化分支并入路由

s2 的锻房只会说散文;本步把 t12 打造的 SwordOrder 数据契约请进来:
forge 分支升级为 prompt | llm | PydanticOutputParser 结构化链,
一次 invoke 直接产出校验过的铸剑单对象。同一路由器下,
不同分支的出口类型可以不同——铭文坊吐 str,锻房吐 SwordOrder。
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
    # ge/le 是范围约束:锋芒值超出 1-100 直接校验失败,脏数据进不了系统
    sharpness: int = Field(ge=1, le=100, description="锋芒值,1-100")
    inscription: str = Field(description="剑身铭文,不超过十二字")


# 解析器即翻译官:LLM 的 JSON 文本 → 校验 → SwordOrder 对象
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
    """意图分类链(s1 的件):出口是原始判定文本。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是铸剑台的接待。判断客人来意,只回答一个词:"
                   "forge(铸剑)、inscribe(题铭文)、appraise(鉴剑)、chat(闲聊)。"),
        ("human", "{request}"),
    ])
    return prompt | build_llm(["forge", "inscribe", "appraise"]) | StrOutputParser()


def normalize_intent(raw: str) -> str:
    """清洗模型输出:包含即命中,不中归 chat。"""
    text = raw.strip().lower()
    for intent in INTENT_OPTIONS:
        if intent in text:
            return intent
    return "chat"


def build_forge_chain():
    """锻房升级版:直接产出校验过的 SwordOrder 对象。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是铸剑大师,按契约输出铸剑单 JSON。"),
        ("human", "客人需求:{request}\n{format_instructions}"),
    ]).partial(format_instructions=parser.get_format_instructions())
    # partial 在组装期固化契约:其中的花括号若当普通变量传入会被二次格式化炸掉;
    # 末端接 parser 而非 StrOutputParser,出口类型就是 SwordOrder
    return prompt | build_llm([MOCK_SWORD_JSON]) | parser


def build_inscribe_chain():
    """铭文坊:为宝剑题铭文,出口是 str。"""
    prompt = ChatPromptTemplate.from_messages([("system", "你是铭文师,题一句四言或七言铭文。"), ("human", "{request}")])
    return prompt | build_llm(["霜刃未曾试,今日把示君。"]) | StrOutputParser()


def build_chat_chain():
    """茶室:闲聊兜底。"""
    prompt = ChatPromptTemplate.from_messages([("system", "你是铸剑台掌柜,陪客人闲聊,谈吐风趣。"), ("human", "{request}")])
    return prompt | build_llm(["坐,炉上正温着茶,慢慢聊。"]) | StrOutputParser()


def build_router():
    """路由器原样复用 s2:分支出口类型变了,路由器一行都不用改。"""
    classify = build_classifier_chain() | normalize_intent
    return RunnablePassthrough.assign(intent=classify) | RunnableBranch(
        (lambda x: x["intent"] == "forge", build_forge_chain()),
        (lambda x: x["intent"] == "inscribe", build_inscribe_chain()),
        build_chat_chain(),
    )


def main() -> None:
    """三客上门:锻房出对象,其余作坊出散文,按类型分派渲染。"""
    router = build_router()
    guests = ["我要铸一柄佩剑", "给此剑题句铭文", "帮我鉴赏这柄古剑"]
    print("== 铸剑台 · 锻房升级 ==")
    for g in guests:
        result = router.invoke({"request": g})
        if isinstance(result, SwordOrder):  # 硬出口:逐字段渲染铸剑单
            print(f"「{g}」→ 锻房出货:{result.name}|{result.material}|锋芒{result.sharpness}|「{result.inscription}」")
        else:  # 软出口:散文原样打印
            print(f"「{g}」→ 答复:{result}")


if __name__ == "__main__":
    main()
