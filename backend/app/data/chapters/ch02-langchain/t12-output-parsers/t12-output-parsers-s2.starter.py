"""铸剑台 · s2:结构化链组装

s1 里"拼提示词 → 调模型 → 手动 parse"是三步散操作;本步用 LCEL 管道符
把它们焊成一条链:输入主题,输出直接就是校验过的 SwordOrder 对象。
"""
import json
import os
import sys

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.language_models.fake import FakeListLLM
from langchain_openai import ChatOpenAI

# 联网前置检查:没有 Key 且未开 MOCK 时给出引导并优雅退出
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
    sharpness: int = Field(ge=1, le=100, description="锋芒值,1-100 的整数")
    inscription: str = Field(description="剑身铭文,不超过十二字")


parser = PydanticOutputParser(pydantic_object=SwordOrder)


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


def build_forge_chain():
    """组装铸剑链:提示词 → 模型 → 解析器,输出直接是 SwordOrder 对象。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一位铸剑大师,为客人设计佩剑。只输出符合契约的 JSON。"),
        ("human", "请以「{theme}」为题设计一柄剑。\n{format_instructions}"),
    ])
    # TODO: 给 prompt 调 .partial(format_instructions=parser.get_format_instructions())
    #       预填格式契约,再用 | 把 prompt、get_llm()、parser 串成链并 return
    # 提示: partial 把"每次调用都不变"的契约在组装期固化,invoke 时只需传 {theme};
    #       若把 format_instructions 留给 invoke 再传,里面的花括号会被二次格式化炸掉
    raise NotImplementedError("build_forge_chain 尚未实现:请按 TODO 提示组装铸剑链")


def forge(theme: str) -> SwordOrder:
    """按主题铸剑:整条链一次 invoke,拿到结构化结果。"""
    chain = build_forge_chain()
    return chain.invoke({"theme": theme})


def main() -> None:
    """开一炉,展示链式调用的完整结构化产出。"""
    order = forge("塞北飞雪")
    print("== 链式铸剑(一次 invoke,直接得到对象) ==")
    print(f"  返回类型 : {type(order).__name__}")
    print(f"  剑名     : {order.name}")
    print(f"  锋芒     : {order.sharpness}/100")
    print("\n== model_dump() 序列化(入库/传输用) ==")
    print(json.dumps(order.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
