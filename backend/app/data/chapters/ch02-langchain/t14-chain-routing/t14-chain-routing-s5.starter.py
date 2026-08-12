"""黑糖资料室 · 项目咨询路由 · s5：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：组装带意图、历史与容错的项目咨询工作台。
# - 补写：补写文本链、路由器与 `workbench`。
# - 关键函数/类（入参 → 出参）：`build_router()` 返回完整路由；`workbench(router, request: str, history)` 注入输入并返回分支结果；`tag(intent: str)` 标记意图。
# - 技术栈：LangChain LCEL、`MessagesPlaceholder`、`RunnableBranch`。
# - 前置条件：真实调用需右上角 DeepSeek API Key；历史必须是 LangChain 消息对象列表。
# - 可观察结果：工作台按意图分流，并能携带已有对话历史。
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
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

INTENT_OPTIONS = ("forge", "inscribe", "appraise", "chat")
MOCK_SWORD_JSON = '{"name": "晨光", "material": "冷色调素材", "sharpness": 92, "inscription": "让创意被看见"}'


class SwordOrder(BaseModel):
    """制作单(t12 的数据契约):制作组的硬出口。"""

    name: str = Field(description="方案名称,两到四个汉字")
    material: str = Field(description="主材,如 冷色调图片/品牌字体/活动图标")
    sharpness: int = Field(ge=1, le=100, description="质量评分,1-100")
    inscription: str = Field(description="方案文案,不超过十二字")


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
        ("system", "你是提示词工作台的接待。判断客人来意,只回答一个词:forge / inscribe / appraise / chat。"),
        ("human", "{request}"),
    ])
    # 函数接在管道末端,自动包装成 RunnableLambda
    return prompt | build_llm(["forge", "inscribe", "appraise", "chat", "forge", "chat"]) | StrOutputParser() | normalize_intent


def normalize_intent(raw: str) -> str:
    text = raw.strip().lower()
    hit = [i for i in INTENT_OPTIONS if i in text]
    return hit[0] if hit else "chat"  # 包含即命中,不中归 chat,脏值进不了分支


def build_forge_chain():
    """制作组(s3 契约 + s4 降级):结构化主链挂散文副链。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是内容策划助手,按契约输出内容方案单 JSON。"),
        ("human", "客人需求:{request}\n{format_instructions}"),
    ]).partial(format_instructions=parser.get_format_instructions())
    # MOCK 剧本:第一流程 JSON 残缺逼出降级,第二流程合格展示恢复
    primary = prompt | build_llm(['{"name": "晨光", "material": "冷色调素材", "sha', MOCK_SWORD_JSON]) | parser
    fallback = ChatPromptTemplate.from_messages([("system", "你是内容策划助手,用三句散文给出内容制作建议。"), ("human", "{request}")]) | build_llm(["[降级] 模型服务繁忙,先使用品牌字体完成基础版式,稍后再补充细节。"]) | StrOutputParser()
    return primary.with_fallbacks([fallback])


def build_text_chain(role: str, mock_reply: str):
    """文案组与质量评审组共用的散文链模具:换个角色就是新工作组。"""
    prompt = ChatPromptTemplate.from_messages([("system", role), ("human", "{request}")])
    return prompt | build_llm([mock_reply]) | StrOutputParser()


def build_chat_chain():
    """咨询台(t13 的件):带问答录的闲聊链,history 槽位平铺历史消息。"""
    # TODO: 拼带问答录的咨询台模板并 return 闲聊链
    # 提示: prompt = ChatPromptTemplate.from_messages([
    #           ("system", "你是黑糖资料室掌柜,陪咨询者闲聊,记得照应上文。"),
    #           MessagesPlaceholder("history"), ("human", "{request}"),  # 可变长历史槽位
    #       ])
    #       return prompt | build_llm(["作品需要多轮评审才能稳定。", "正是此意,制作如学习。"]) | StrOutputParser()
    raise NotImplementedError("build_chat_chain 尚未实现:请按 TODO 提示拼带问答录的闲聊链")


def tag(intent: str):
    return RunnableLambda(lambda reply: (intent, reply))  # (意图, 答复) 元组统一全台契约


def build_router():
    """总装:assign 判来意 → RunnableBranch 分流 → 各出口接 tag 打标签。"""
    # TODO: 组装四路总装路由器:assign 判来意 → RunnableBranch 按序分流 → 各出口接 tag 打标签
    # 提示: return RunnablePassthrough.assign(intent=build_classifier_chain()) | RunnableBranch(
    #           (lambda x: x["intent"] == "forge", build_forge_chain() | tag("forge")),
    #           (lambda x: x["intent"] == "inscribe", build_text_chain("你是文案师,题一句四言或七言文案。", "让创意被看见,今日把示君。") | tag("inscribe")),
    #           (lambda x: x["intent"] == "appraise", build_text_chain("你是质量评审员,从材质、工艺、气韵品鉴。", "这份方案铁质温润,包浆厚重,当为前朝旧物。") | tag("appraise")),
    #           build_chat_chain() | tag("chat"))  # 默认分支兜底
    raise NotImplementedError("build_router 尚未实现:请按 TODO 提示组装总装路由器")


def workbench(router, request: str, history: list) -> None:
    """工作台统一入口:分流接待、渲染答复,闲聊记入问答录。"""
    # TODO: 接待一位咨询者:打印、分流、渲染,闲聊登记入问答录
    # 提示: print(f"咨询者:「{request}」")
    #       intent, reply = router.invoke({"request": request, "history": list(history)})  # history 传拷贝:模型看到接待前的快照
    #       reply 是 SwordOrder 时格式化成 f"制作单 · {reply.name}({reply.material},质量{reply.sharpness}):「{reply.inscription}」"
    #       print(f"  [{intent}] {reply}")
    #       if intent == "chat":  # 只登记闲聊问答,一问一答各一条
    #           history.append(HumanMessage(content=request)); history.append(AIMessage(content=reply))
    raise NotImplementedError("workbench 尚未实现:请按 TODO 提示完成工作台接待流程")


def main() -> None:
    """开张演练:六客轮番上门,含一次制作组降级、两轮闲聊。"""
    router, history = build_router(), []
    guests = ["我要制作一份活动主视觉", "为这份方案写一句短文案", "帮我鉴赏这份旧版设计", "你觉得好方案的标准是什么?", "再制作一份更好的", "刚才说作品需要评审,具体指什么?"]
    print("== 提示词工作台 · 开张大吉 ==")
    for g in guests:
        workbench(router, g, history)
    print(f"\n== 打烊盘点:问答录共 {len(history)} 条 ==")
    for m in history:
        print(f"  {m.type}: {m.content}")


if __name__ == "__main__":
    main()
