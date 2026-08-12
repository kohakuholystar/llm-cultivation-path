"""黑糖资料室 · 项目咨询路由 · s4：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：为结构化分支配置 `with_fallbacks`，让失败有明确退路。
# - 补写：补写主链、备用链和路由器。
# - 关键函数/类（入参 → 出参）：`build_structured_forge_chain()` 返回主链；`build_fallback_forge_chain()` 返回文本退路；`build_forge_chain()` 组合 fallback。
# - 技术栈：LangChain Runnable、`with_fallbacks`、Pydantic。
# - 前置条件：真实调用需右上角 DeepSeek API Key；备用链处理的是主链异常。
# - 可观察结果：解析失败时仍能返回可用的降级结果。
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
    sharpness: int = Field(ge=1, le=100, description="质量评分,1-100")
    inscription: str = Field(description="方案文案,不超过十二字")


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
    """意图分类链:本步剧本判出 制作 → 文案 → 制作。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是提示词工作台的接待。判断客人来意,只回答一个词:"
                   "forge(内容制作)、inscribe(撰写文案)、appraise(质量评审)、chat(闲聊)。"),
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
    """制作组主链:产出 SwordOrder;JSON 不合格会抛 OutputParserException。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是内容策划助手,按契约输出内容方案单 JSON。"),
        ("human", "客人需求:{request}\n{format_instructions}"),
    ]).partial(format_instructions=parser.get_format_instructions())
    # MOCK 剧本:第一流程 JSON 残缺(逼出降级),第二流程合格(展示恢复)
    return prompt | build_llm(['{"name": "晨光", "material": "冷色调素材", "sha', MOCK_SWORD_JSON]) | parser


def build_fallback_forge_chain():
    """制作组副链:不要契约只要人话,故障面更小,兜底用。"""
    # TODO: 拼一条散文副链并 return,故障面更小,兜底用
    # 提示: prompt = ChatPromptTemplate.from_messages([
    #           ("system", "你是制作大师,用三句散文给出制作建议。"),
    #           ("human", "{request}"),  # 输入变量必须与主链一致,否则降级时再炸一次
    #       ])
    #       return prompt | build_llm(["[降级] 流程火正旺,且以品牌字体打底,徐徐图之。"]) | StrOutputParser()
    raise NotImplementedError("build_fallback_forge_chain 尚未实现:请按 TODO 提示拼散文副链")


def build_forge_chain():
    """主链挂副链:主链抛异常时自动降级,咨询者绝不空手而归。"""
    # TODO: 把结构化主链挂上散文副链并 return
    # 提示: return build_structured_forge_chain().with_fallbacks([build_fallback_forge_chain()])
    #       with_fallbacks 的参数是 Runnable 的【列表】,按序尝试;默认捕获所有 Exception
    raise NotImplementedError("build_forge_chain 尚未实现:请按 TODO 提示挂上降级副链")


def build_inscribe_chain():
    """文案组:为内容方案撰写文案。"""
    prompt = ChatPromptTemplate.from_messages([("system", "你是文案师,题一句四言或七言文案。"), ("human", "{request}")])
    return prompt | build_llm(["让创意被看见,今日把示君。"]) | StrOutputParser()


def build_router():
    """路由器照旧:挂了降级的制作组链对上游完全透明。"""
    classify = build_classifier_chain() | normalize_intent
    return RunnablePassthrough.assign(intent=classify) | RunnableBranch(
        (lambda x: x["intent"] == "forge", build_forge_chain()),
        (lambda x: x["intent"] == "inscribe", build_inscribe_chain()),
        build_inscribe_chain(),  # 默认分支
    )


def main() -> None:
    """两次制作:第一流程降级为散文,第二流程恢复正常出制作单。"""
    router = build_router()
    guests = ["我要制作一份活动主视觉", "为这份方案写一句短文案", "再制作一份更好的"]
    print("== 提示词工作台 · 备用链演练 ==")
    for g in guests:
        result = router.invoke({"request": g})
        if isinstance(result, SwordOrder):
            print(f"「{g}」→ 主链出货 · 内容方案单:{result.name}|质量{result.sharpness}")
        else:  # 副链散文自带 [降级] 标记:主链失手,备用流程顶上
            print(f"「{g}」→ {result}")


if __name__ == "__main__":
    main()
