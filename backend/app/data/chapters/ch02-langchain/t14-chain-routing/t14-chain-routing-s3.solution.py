"""黑糖资料室 · 项目咨询路由 · s3：用 LangChain 完成可验证的学习任务。"""
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
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

INTENT_OPTIONS = ("forge", "inscribe", "appraise", "chat")
MOCK_SWORD_JSON = '{"name": "晨光", "material": "冷色调素材", "sharpness": 92, "inscription": "让创意被看见"}'


class SwordOrder(BaseModel):
    """制作单(t12 的数据契约):制作组的硬出口。"""

    name: str = Field(description="方案名称,两到四个汉字")
    material: str = Field(description="主材,如 冷色调图片/品牌字体/活动图标")
    # ge/le 是范围约束:质量评分超出 1-100 直接校验失败,脏数据进不了系统
    sharpness: int = Field(ge=1, le=100, description="质量评分,1-100")
    inscription: str = Field(description="方案文案,不超过十二字")


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
        ("system", "你是提示词工作台的接待。判断客人来意,只回答一个词:"
                   "forge(内容制作)、inscribe(撰写文案)、appraise(质量评审)、chat(闲聊)。"),
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
    """制作组升级版:直接产出校验过的 SwordOrder 对象。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是内容策划助手,按契约输出内容方案单 JSON。"),
        ("human", "客人需求:{request}\n{format_instructions}"),
    ]).partial(format_instructions=parser.get_format_instructions())
    # partial 在组装期固化契约:其中的花括号若当普通变量传入会被二次格式化炸掉;
    # 末端接 parser 而非 StrOutputParser,出口类型就是 SwordOrder
    return prompt | build_llm([MOCK_SWORD_JSON]) | parser


def build_inscribe_chain():
    """文案组:为内容方案撰写文案,出口是 str。"""
    prompt = ChatPromptTemplate.from_messages([("system", "你是文案师,题一句四言或七言文案。"), ("human", "{request}")])
    return prompt | build_llm(["让创意被看见,今日把示君。"]) | StrOutputParser()


def build_chat_chain():
    """咨询台:闲聊兜底。"""
    prompt = ChatPromptTemplate.from_messages([("system", "你是提示词工作台掌柜,陪客人闲聊,谈吐风趣。"), ("human", "{request}")])
    return prompt | build_llm(["坐,处理器上正温着茶,慢慢聊。"]) | StrOutputParser()


def build_router():
    """路由器原样复用 s2:分支出口类型变了,路由器一行都不用改。"""
    classify = build_classifier_chain() | normalize_intent
    return RunnablePassthrough.assign(intent=classify) | RunnableBranch(
        (lambda x: x["intent"] == "forge", build_forge_chain()),
        (lambda x: x["intent"] == "inscribe", build_inscribe_chain()),
        build_chat_chain(),
    )


def main() -> None:
    """三客上门:制作组出对象,其余工作组出散文,按类型分派渲染。"""
    router = build_router()
    guests = ["我要制作一份活动主视觉", "为这份方案写一句短文案", "帮我鉴赏这份旧版设计"]
    print("== 提示词工作台 · 内容制作组升级 ==")
    for g in guests:
        result = router.invoke({"request": g})
        if isinstance(result, SwordOrder):  # 硬出口:逐字段渲染制作单
            print(f"「{g}」→ 内容制作组出货:{result.name}|{result.material}|质量{result.sharpness}|「{result.inscription}」")
        else:  # 软出口:散文原样打印
            print(f"「{g}」→ 答复:{result}")


if __name__ == "__main__":
    main()
