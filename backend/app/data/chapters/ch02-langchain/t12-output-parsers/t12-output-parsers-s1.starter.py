"""铸剑台 · s1:铸剑单契约

LLM 天生只会说"散文",而铸剑台需要的是能入库、能校验的结构化铸剑单。
本步用 Pydantic 模型定义数据契约,再用 PydanticOutputParser 完成
"文本 → 强类型对象"的转换——这是整个铸剑台的第一块基石。
"""
import os
import sys

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.language_models.fake import FakeListLLM
from langchain_openai import ChatOpenAI

# 联网前置检查:没有 Key 且未开 MOCK 时给出引导并优雅退出,不让学习者面对 traceback
if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[铸剑台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

MOCK_SWORD_JSON = (
    '{"name": "青霜", "material": "寒铁", "sharpness": 92, "inscription": "霜刃未曾试"}'
)


class SwordOrder(BaseModel):
    """一柄剑的铸剑单:铸剑台全链路的统一数据契约。"""

    name: str = Field(description="剑名,两到四个汉字,要有古意")
    material: str = Field(description="主材,如 寒铁/玄钢/陨星砂")
    # TODO: 补上锋芒值字段:sharpness: int,用 Field(ge=1, le=100, description=...) 约束在 1-100
    # 提示: 数值字段必须声明数值类型 + 范围约束,否则「锋芒:极高」也能混进来,契约形同虚设
    inscription: str = Field(description="剑身铭文,不超过十二字")


# TODO: 创建解析器实例 parser = PydanticOutputParser(pydantic_object=SwordOrder)
# 提示: 解析器是模块级常量,放在 SwordOrder 类定义之后、get_llm 之前;
#       建好后可用 parser.get_format_instructions() 取到给 LLM 看的 JSON Schema 说明


def get_llm():
    """MOCK_LLM 时返回假模型便于离线演示;否则返回指向 DeepSeek 的 ChatOpenAI。"""
    if os.environ.get("MOCK_LLM"):
        return FakeListLLM(responses=[MOCK_SWORD_JSON])
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0.8,
    )


def design_brief(theme: str) -> str:
    """铸剑需求描述:把 parser 的格式契约一并交给 LLM。"""
    # get_format_instructions() 会生成一段说明,告诉模型必须输出哪种 JSON
    return (
        f"你是一位铸剑大师。请以「{theme}」为题设计一柄剑。\n"
        f"{parser.get_format_instructions()}"
    )


def main() -> None:
    """让 LLM 开一炉,并把返回文本解析成强类型对象。"""
    raw = get_llm().invoke(design_brief("雪夜孤城"))  # LLM 的原始文本
    # TODO: 用 parser.parse(raw) 把文本解析成 SwordOrder 对象并逐字段打印(剑名/主材/锋芒/铭文)
    # 提示: order = parser.parse(raw);返回的是模型实例不是 dict,
    #       用 order.name / order.material / order.sharpness / order.inscription 点号取字段


if __name__ == "__main__":
    main()
