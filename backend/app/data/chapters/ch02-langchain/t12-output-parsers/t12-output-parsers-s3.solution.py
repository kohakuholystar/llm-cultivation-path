"""黑糖资料室 · 结构化输出验收 · s3：用 LangChain 完成可验证的学习任务。"""
import os
import sys

from pydantic import BaseModel, Field
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.language_models.fake import FakeListLLM
from langchain_openai import ChatOpenAI

# 联网前置检查:没有 Key 且未开 MOCK 时给出引导并优雅退出
if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

# MOCK 剧情:第一流程烧出散文废料,第二流程才出合规 JSON(演示重试全过程)
MOCK_RESPONSES = [
    "好的!这份方案名称叫晨光,材料是冷色调素材,质量九十二,文案让创意被看见。",
    '{"name": "晨光", "material": "冷色调素材", "sharpness": 92, "inscription": "让创意被看见"}',
]


class SwordOrder(BaseModel):
    """一份方案的制作单:黑糖资料室全链路的统一数据契约。"""

    name: str = Field(description="方案名称,两到四个汉字,要有古意")
    material: str = Field(description="主材,如 冷色调图片/品牌字体/活动图标")
    sharpness: int = Field(ge=1, le=100, description="质量评分,1-100 的整数")
    inscription: str = Field(description="方案文案,不超过十二字")


parser = PydanticOutputParser(pydantic_object=SwordOrder)


def repair_once(raw, error: Exception, llm) -> SwordOrder:
    """把原输出、解析错误和契约显式交给模型，进行一次修复。"""
    text = getattr(raw, "content", raw)
    repair_prompt = (
        "只返回符合下列 JSON Schema 的 JSON，不要解释。\n"
        f"解析错误：{error}\n原输出：{text}\n{parser.get_format_instructions()}"
    )
    fixed = llm.invoke(repair_prompt)
    return parser.parse(getattr(fixed, "content", fixed))


def get_llm():
    """MOCK_LLM 时返回假模型便于离线演示;否则返回指向 DeepSeek 的 ChatOpenAI。"""
    if os.environ.get("MOCK_LLM"):
        return FakeListLLM(responses=MOCK_RESPONSES)
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0.8,
    )


def build_prompt():
    """制作提示词:契约在组装期用 partial 固化。"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", "你是一位内容策划助手,为客人设计活动主视觉。只输出符合契约的 JSON。"),
            ("human", "请以「{theme}」为题设计一份方案。\n{format_instructions}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())


def forge_with_retry(theme: str) -> SwordOrder:
    """带重试的制作:解析失败时把错误喂回模型,最多回流程 max_retries 次。"""
    prompt = build_prompt()
    llm = get_llm()
    # 修复提示需要"原始输入是什么",所以手动拿 PromptValue 再 invoke,不走 | 管道
    prompt_value = prompt.format_prompt(theme=theme)
    completion = llm.invoke(prompt_value)  # 第一次启动:可能是散文
    print(f"  [处理器前记录] 原始输出:{str(completion)[:50]}...")
    try:
        return parser.parse(getattr(completion, "content", completion))
    except OutputParserException as error:
        return repair_once(completion, error, llm)


def main() -> None:
    """开一流程,观察"散文 → 报错 → 模型自我修复 → 通过"的全过程。"""
    print("== 带重试的内容制作链 ==")
    order = forge_with_retry("雪夜孤城")
    print(f"  生成方案名称 : {order.name}")
    print(f"  主材     : {order.material}")
    print(f"  质量     : {order.sharpness}/100")
    print(f"  文案     : {order.inscription}")
    print("  (MOCK 剧情里,这份 JSON 是模型看到报错后自己重写的)")


if __name__ == "__main__":
    main()
