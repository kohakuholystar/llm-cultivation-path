"""铸剑台 · s5:开张大吉 —— 工作台总装

章项目收官:分类链判来意、RunnableBranch 分流、结构化链立契约、fallbacks 保底线、MessagesPlaceholder 记问答,全部焊进一台工作台。
"""
import os
import sys

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

MOCK_LLM = os.environ.get("MOCK_LLM") == "1"

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
    return ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
                      base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                      api_key=os.environ["OPENAI_API_KEY"], temperature=0)


def build_classifier_chain():
    """分类链(s1 的件):判定 + 清洗焊成一道,出口是干净的意图词。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是铸剑台的接待。判断客人来意,只回答一个词:forge / inscribe / appraise / chat。"),
        ("human", "{request}"),
    ])
    # 函数接在管道末端,自动包装成 RunnableLambda
    return prompt | build_llm(["forge", "inscribe", "appraise", "chat", "forge", "chat"]) | StrOutputParser() | normalize_intent


def normalize_intent(raw: str) -> str:
    text = raw.strip().lower()
    hit = [i for i in INTENT_OPTIONS if i in text]
    return hit[0] if hit else "chat"  # 包含即命中,不中归 chat,脏值进不了分支


def build_forge_chain():
    """锻房(s3 契约 + s4 降级):结构化主链挂散文副链。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是铸剑大师,按契约输出铸剑单 JSON。"),
        ("human", "客人需求:{request}\n{format_instructions}"),
    ]).partial(format_instructions=parser.get_format_instructions())
    # MOCK 剧本:第一炉 JSON 残缺逼出降级,第二炉合格展示恢复
    primary = prompt | build_llm(['{"name": "青霜", "material": "寒铁", "sha', MOCK_SWORD_JSON]) | parser
    fallback = ChatPromptTemplate.from_messages([("system", "你是铸剑大师,用三句散文给出铸剑建议。"), ("human", "{request}")]) | build_llm(["[降级] 炉火正旺,且以玄钢打底,徐徐图之。"]) | StrOutputParser()
    return primary.with_fallbacks([fallback])


def build_text_chain(role: str, mock_reply: str):
    """铭文坊与鉴剑斋共用的散文链模具:换个角色就是新作坊。"""
    prompt = ChatPromptTemplate.from_messages([("system", role), ("human", "{request}")])
    return prompt | build_llm([mock_reply]) | StrOutputParser()


def build_chat_chain():
    """茶室(t13 的件):带问答录的闲聊链,history 槽位平铺历史消息。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是铸剑台掌柜,陪客人闲聊,记得照应上文。"),
        MessagesPlaceholder("history"), ("human", "{request}"),  # 可变长历史槽位
    ])
    return prompt | build_llm(["剑如人,千锤百炼方成器。", "正是此意,铸剑如修行。"]) | StrOutputParser()


def tag(intent: str):
    return RunnableLambda(lambda reply: (intent, reply))  # (意图, 答复) 元组统一全台契约


def build_router():
    """总装:assign 判来意 → RunnableBranch 分流 → 各出口接 tag 打标签。"""
    return RunnablePassthrough.assign(intent=build_classifier_chain()) | RunnableBranch(
        (lambda x: x["intent"] == "forge", build_forge_chain() | tag("forge")),
        (lambda x: x["intent"] == "inscribe", build_text_chain("你是铭文师,题一句四言或七言铭文。", "霜刃未曾试,今日把示君。") | tag("inscribe")),
        (lambda x: x["intent"] == "appraise", build_text_chain("你是鉴剑师,从材质、工艺、气韵品鉴。", "此剑铁质温润,包浆厚重,当为前朝旧物。") | tag("appraise")),
        build_chat_chain() | tag("chat"),  # 默认分支兜底
    )


def workbench(router, request: str, history: list) -> None:
    """工作台统一入口:分流接待、渲染答复,闲聊记入问答录。"""
    print(f"客人:「{request}」")
    # history 传拷贝:模型看到接待前的快照,本次问答接待完再登记
    intent, reply = router.invoke({"request": request, "history": list(history)})
    if isinstance(reply, SwordOrder):
        reply = f"铸剑单 · {reply.name}({reply.material},锋芒{reply.sharpness}):「{reply.inscription}」"
    print(f"  [{intent}] {reply}")
    if intent == "chat":  # 只登记闲聊问答,一问一答各一条
        history.append(HumanMessage(content=request))
        history.append(AIMessage(content=reply))


def main() -> None:
    """开张演练:六客轮番上门,含一次锻房降级、两轮闲聊。"""
    router, history = build_router(), []
    guests = ["我要铸一柄佩剑", "给此剑题句铭文", "帮我鉴赏这柄古剑", "你觉得剑是什么?", "再铸一柄更好的", "方才说剑如人,此话怎讲?"]
    print("== 铸剑台 · 开张大吉 ==")
    for g in guests:
        workbench(router, g, history)
    print(f"\n== 打烊盘点:问答录共 {len(history)} 条 ==")
    for m in history:
        print(f"  {m.type}: {m.content}")


if __name__ == "__main__":
    main()
