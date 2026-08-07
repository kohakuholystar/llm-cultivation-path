"""铸剑台 · s4:武林帖格式

内置解析器只认 JSON,但铸剑台收到一批武林老帖:中文「键:值」四行帖。
本步继承 BaseOutputParser 手写 ForgeCardParser,让链的末端直接吐出
SwordOrder 对象——自定义解析器与内置解析器在 LCEL 链里完全同权。
"""
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
    print("[铸剑台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

MOCK_CARD = "【铸剑帖】\n剑名:青霜\n主材:寒铁\n锋芒:92\n铭文:霜刃未曾试"


class SwordOrder(BaseModel):
    """一柄剑的铸剑单:铸剑台全链路的统一数据契约。"""

    name: str = Field(description="剑名,两到四个汉字,要有古意")
    material: str = Field(description="主材,如 寒铁/玄钢/陨星砂")
    sharpness: int = Field(ge=1, le=100, description="锋芒值,1-100 的整数")
    inscription: str = Field(description="剑身铭文,不超过十二字")


# 帖面中文键 → 契约字段名 的映射表:表示层与数据契约之间的翻译层
KEY_MAP = {"剑名": "name", "主材": "material", "锋芒": "sharpness", "铭文": "inscription"}


class ForgeCardParser(BaseOutputParser):
    """铸剑帖解析器:把「键:值」四行帖解析成 SwordOrder。"""

    def parse(self, text: str) -> SwordOrder:
        # TODO: 逐行解析 text:含「:」的行用 line.partition(":") 切键值,经 KEY_MAP 映射收进 data;
        #       缺字段或锋芒非整数时 raise OutputParserException(...);最后 return SwordOrder(**data)
        # 提示: 跳过不含冒号的行(如【铸剑帖】标题行);key.strip() 后查 KEY_MAP;
        #       字段到齐后 data["sharpness"] = int(data["sharpness"]) 转数值,
        #       再 return SwordOrder(**data) 交给 Pydantic 做契约校验(如锋芒 1-100)
        raise NotImplementedError("ForgeCardParser.parse 尚未实现:请按 TODO 提示解析铸剑帖")

    def get_format_instructions(self) -> str:
        # TODO: 返回中文格式说明,要求模型按「剑名:.. / 主材:.. / 锋芒:.. / 铭文:..」逐行输出
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
    """组装铸剑帖链:提示词 → 模型 → 自定义解析器,末端直接是 SwordOrder。"""
    card_parser = ForgeCardParser()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一位铸剑大师,只用古老的铸剑帖格式回帖。"),
            ("human", "请以「{theme}」为题设计一柄剑。\n{format_instructions}"),
        ]
    ).partial(format_instructions=card_parser.get_format_instructions())
    return prompt | get_llm() | card_parser


def main() -> None:
    """开一炉验证自定义解析器;再演示一次报错路径。"""
    order = build_card_chain().invoke({"theme": "江南烟雨"})
    print("== 铸剑帖解析成功 ==")
    print(f"  剑名:{order.name}  主材:{order.material}")
    print(f"  锋芒:{order.sharpness}/100  铭文:{order.inscription}")
    print("\n== 坏帖拦截演示(缺字段) ==")
    try:
        ForgeCardParser().parse("剑名:断水\n主材:玄钢")
    except OutputParserException as exc:
        print(f"  拦下坏帖 → OutputParserException: {exc}")


if __name__ == "__main__":
    main()
