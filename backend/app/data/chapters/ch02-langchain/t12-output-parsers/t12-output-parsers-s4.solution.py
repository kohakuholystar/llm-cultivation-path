"""黑糖资料室 · 结构化输出验收 · s4：用 LangChain 完成可验证的学习任务。"""
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
        data: dict = {}
        for line in text.strip().splitlines():
            if ":" not in line:
                continue  # 跳过【制作帖】标题行等非键值行
            key, _, value = line.partition(":")  # 只按第一个冒号切,文案里含冒号也安全
            field = KEY_MAP.get(key.strip())
            if field:
                data[field] = value.strip()
        missing = [f for f in KEY_MAP.values() if f not in data]
        if missing:
            # 解析器报错的官方协议:OutputParserException,上层重试/修复只认它
            raise OutputParserException(f"内容制作帖缺字段: {missing}")
        try:
            data["sharpness"] = int(data["sharpness"])
        except ValueError as exc:
            raise OutputParserException(f"质量评分不是整数: {data['sharpness']}") from exc
        return SwordOrder(**data)  # Pydantic 再做一次契约校验(如质量 1-100)

    def get_format_instructions(self) -> str:
        return (
            "请严格按以下格式输出内容制作帖,每行一个字段,不要输出任何其他内容:\n"
            "方案名称:<方案名称>\n主材:<主材>\n质量:<1-100的整数>\n文案:<文案>"
        )

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
        temperature=0,
    )


def build_card_chain():
    """组装制作帖链:提示词 → 模型 → 自定义解析器,末端直接是 SwordOrder。"""
    card_parser = ForgeCardParser()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一位内容策划助手,只用古老的内容制作帖格式回帖；质量必须是 1 到 100 的 ASCII 阿拉伯数字,不能写中文数字。"),
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
