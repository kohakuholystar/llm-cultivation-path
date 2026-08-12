"""黑糖资料室 · 结构化输出验收 · s4：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：实现自定义解析器，把特定文本格式转换为数据对象。
# - 补写：补写 `ForgeCardParser` 的解析逻辑和链。
# - 关键函数/类（入参 → 出参）：`ForgeCardParser.parse(text: str) -> SwordOrder` 解析文本；`build_card_chain()` 返回使用自定义 parser 的链。
# - 技术栈：LangChain Core 自定义输出解析器、Pydantic。
# - 前置条件：本步可用 mock 演示；输入文本必须满足卡片格式。
# - 可观察结果：卡片文本被转换为经过字段校验的数据对象。
import os
import sys

from pydantic import BaseModel, Field
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.fake import FakeListLLM
from langchain_openai import ChatOpenAI

# 联网前置检查:没有 Key 且未开 MOCK 时给出引导并优雅退出
if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

MOCK_CARD = "【内容制作帖】\n方案名称:晨光\n主材:冷色调素材\n质量:92\n文案:让创意被看见"


class SwordOrder(BaseModel):
    """一份方案的制作单:黑糖资料室全链路的统一数据契约。"""

    name: str = Field(description="方案名称,两到四个汉字,要有古意")
    material: str = Field(description="主材,如 冷色调图片/品牌字体/活动图标")
    sharpness: int = Field(ge=1, le=100, description="质量评分,1-100 的整数")
    inscription: str = Field(description="方案文案,不超过十二字")


# 帖面中文键 → 契约字段名 的映射表:表示层与数据契约之间的翻译层
KEY_MAP = {"方案名称": "name", "主材": "material", "质量": "sharpness", "文案": "inscription"}


class ForgeCardParser(BaseOutputParser):
    """制作帖解析器:把「键:值」四行帖解析成 SwordOrder。"""

    def parse(self, text: str) -> SwordOrder:
        # TODO: 逐行解析 text:含「:」的行用 line.partition(":") 切键值,经 KEY_MAP 映射收进 data;
        #       缺字段或质量非整数时 raise OutputParserException(...);最后 return SwordOrder(**data)
        # 提示: 跳过不含冒号的行(如【制作帖】标题行);key.strip() 后查 KEY_MAP;
        #       字段到齐后 data["sharpness"] = int(data["sharpness"]) 转数值,
        #       再 return SwordOrder(**data) 交给 Pydantic 做契约校验(如质量 1-100)
        raise NotImplementedError("ForgeCardParser.parse 尚未实现:请按 TODO 提示解析内容制作帖")

    def get_format_instructions(self) -> str:
        # TODO: 返回中文格式说明,要求模型按「方案名:.. / 主材:.. / 质量:.. / 文案:..」逐行输出
        # 提示: 说明里的每个字符都是契约的一部分——要求模型用「:」,解析时也只认「:」,
        #       中英文冒号混用会让模型严格照做反而全部解析失败
        raise NotImplementedError("get_format_instructions 尚未实现:请按 TODO 提示输出格式说明")

    @property
    def _type(self) -> str:
        return "forge_card"  # 序列化标识,LangChain 内部使用


def get_llm():
    """MOCK_LLM 时返回假模型便于离线演示;否则返回指向 DeepSeek 的 ChatOpenAI。"""
    if os.environ.get("MOCK_LLM"):
        return FakeListLLM(responses=[MOCK_CARD])
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0.8,
    )


def build_card_chain():
    """组装制作帖链:提示词 → 模型 → 自定义解析器,末端直接是 SwordOrder。"""
    card_parser = ForgeCardParser()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一位内容策划助手,只用古老的内容制作帖格式回帖。"),
            ("human", "请以「{theme}」为题设计一份方案。\n{format_instructions}"),
        ]
    ).partial(format_instructions=card_parser.get_format_instructions())
    return prompt | get_llm() | card_parser


def main() -> None:
    """开一流程验证自定义解析器;再演示一次报错路径。"""
    order = build_card_chain().invoke({"theme": "江南烟雨"})
    print("== 内容制作帖解析成功 ==")
    print(f"  方案名称:{order.name}  主材:{order.material}")
    print(f"  质量:{order.sharpness}/100  文案:{order.inscription}")
    print("\n== 坏帖拦截演示(缺字段) ==")
    try:
        ForgeCardParser().parse("方案名称:断水\n主材:品牌字体")
    except OutputParserException as exc:
        print(f"  拦下坏帖 → OutputParserException: {exc}")


if __name__ == "__main__":
    main()
