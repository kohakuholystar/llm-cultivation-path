"""铸剑台 · s5:三层防线

线上没有"永远守规矩"的模型:多余的客套话、被截断的 JSON、越界的数值……
本步给铸剑台装上三层防线:严格解析 → 正则提取 → OutputFixingParser 让
LLM 自己把输出修成契约格式。任何一层成功即放行,并记录是哪一层通过的。
"""
import os
import re
import sys

from pydantic import BaseModel, Field
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.language_models.fake import FakeListLLM
from langchain_classic.output_parsers.fix import OutputFixingParser
from langchain_openai import ChatOpenAI

# 联网前置检查:没有 Key 且未开 MOCK 时给出引导并优雅退出
if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[铸剑台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

# MOCK 剧情:第一炉回复又啰嗦又有错(锋芒 999 越界),第二炉才是修好的 JSON
MOCK_RESPONSES = ['回禀东家:{"name": "青霜", "material": "寒铁", "sharpness": 999, "inscription": "霜刃未曾试"},请您过目!',
                  '{"name": "青霜", "material": "寒铁", "sharpness": 92, "inscription": "霜刃未曾试"}']


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
        return FakeListLLM(responses=MOCK_RESPONSES)
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0.8,
    )


def robust_parse(raw: str, llm):
    """三层防线解析 LLM 输出,返回 (SwordOrder, 通关防线名)。"""
    # 第一层:严格解析——输出恰好是干净 JSON 时零成本通过
    try:
        return parser.parse(raw), "第一层·严格解析"
    except OutputParserException:
        pass
    # 第二层:正则提取——从散文里抠出第一个 {...} 片段再解析(re.S 让 . 匹配换行)
    match = re.search(r"\{.*\}", raw, re.S)
    if match:
        try:
            return parser.parse(match.group(0)), "第二层·正则提取"
        except OutputParserException:
            pass  # 抠出来了但内容违约(如锋芒 999),继续降级
    # 第三层:LLM 修复——把错误和原输出交给模型,让它按契约重写
    fixing = OutputFixingParser.from_llm(parser=parser, llm=llm)
    return fixing.parse(raw), "第三层·LLM 修复"


def main() -> None:
    """开一炉,展示三层防线如何接力拦下脏输出。"""
    llm = get_llm()
    raw = llm.invoke("请以「塞北飞雪」为题开一张铸剑单。")
    print(f"== 原始输出 ==\n{raw}\n")
    order, route = robust_parse(raw, llm)
    print(f"== 解析成功({route}) ==")
    print(f"  剑名 : {order.name}")
    print(f"  主材 : {order.material}")
    print(f"  锋芒 : {order.sharpness}/100")
    print(f"  铭文 : {order.inscription}")
    print("  (一层败于散文包裹,二层败于锋芒越界,三层 LLM 修复通过)")


if __name__ == "__main__":
    main()
