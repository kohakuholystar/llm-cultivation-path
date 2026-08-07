"""铸剑台 · s3:回炉重铸

模型是概率机器:哪怕格式说明写得再清楚,偶尔也会输出散文。
RetryWithErrorOutputParser 的思路是"让模型修自己":解析失败时,把
原始输出 + 错误信息 + 格式要求打包发回 LLM,请它按契约重写。
"""
import os
import sys

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.language_models.fake import FakeListLLM
from langchain_classic.output_parsers.retry import RetryWithErrorOutputParser
from langchain_openai import ChatOpenAI

# 联网前置检查:没有 Key 且未开 MOCK 时给出引导并优雅退出
if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[铸剑台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

# MOCK 剧情:第一炉烧出散文废料,第二炉才出合规 JSON(演示重试全过程)
MOCK_RESPONSES = [
    "好的!这柄剑名叫青霜,材料是寒铁,锋芒九十二,铭文霜刃未曾试。",
    '{"name": "青霜", "material": "寒铁", "sharpness": 92, "inscription": "霜刃未曾试"}',
]


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


def build_prompt():
    """铸剑提示词:契约在组装期用 partial 固化。"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", "你是一位铸剑大师,为客人设计佩剑。只输出符合契约的 JSON。"),
            ("human", "请以「{theme}」为题设计一柄剑。\n{format_instructions}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())


def forge_with_retry(theme: str) -> SwordOrder:
    """带重试的铸剑:解析失败时把错误喂回模型,最多回炉 max_retries 次。"""
    prompt = build_prompt()
    llm = get_llm()
    # 重试解析器:内层仍是 parser,失败时用 llm 按"原输出+报错"重写后再试
    retry_parser = RetryWithErrorOutputParser.from_llm(
        parser=parser, llm=llm, max_retries=2
    )
    # 修复提示需要"原始输入是什么",所以手动拿 PromptValue 再 invoke,不走 | 管道
    prompt_value = prompt.format_prompt(theme=theme)
    completion = llm.invoke(prompt_value)  # 第一次开炉:可能是散文
    print(f"  [炉前记录] 原始输出:{str(completion)[:50]}...")
    # parse_with_prompt 内部:parse 失败 → 组装修复提示 → llm 重写 → 再 parse
    return retry_parser.parse_with_prompt(completion, prompt_value)


def main() -> None:
    """开一炉,观察"散文 → 报错 → 模型自我修复 → 通过"的全过程。"""
    print("== 带重试的铸剑链 ==")
    order = forge_with_retry("雪夜孤城")
    print(f"  铸成剑名 : {order.name}")
    print(f"  主材     : {order.material}")
    print(f"  锋芒     : {order.sharpness}/100")
    print(f"  铭文     : {order.inscription}")
    print("  (MOCK 剧情里,这份 JSON 是模型看到报错后自己重写的)")


if __name__ == "__main__":
    main()
