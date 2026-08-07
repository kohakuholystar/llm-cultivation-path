"""铸剑台 · s6:终版 —— 结构化铸剑流水线

把前五步的部件总装成铸剑台的最终形态:
契约(SwordOrder)→ 链(prompt 组装)→ 重试(RetryWithError)
→ 修复(OutputFixing 三层防线)。主流程一条直线,异常全部汇入 robust_parse。
"""
import os
import re
import sys

from pydantic import BaseModel, Field
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.fake import FakeListLLM
from langchain_classic.output_parsers.retry import RetryWithErrorOutputParser
from langchain_classic.output_parsers.fix import OutputFixingParser
from langchain_openai import ChatOpenAI

# 联网前置检查:没有 Key 且未开 MOCK 时给出引导并优雅退出
if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[铸剑台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

# MOCK 剧情:第一炉散文废料,重试后第二炉出合规 JSON
MOCK_RESPONSES = [
    "这柄剑唤作龙吟,玄钢打造,锋利得很!",
    '{"name": "龙吟", "material": "玄钢", "sharpness": 88, "inscription": "龙吟四海"}',
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


def robust_parse(raw: str, llm):
    """三层防线(终版兜底):严格解析 → 正则提取 → LLM 修复。"""
    # TODO: 照 s5 写三层防线并返回 (结果, 通关层名):
    #       1) try parser.parse(raw),成功 return (结果, "严格解析");
    #       2) re.search(r"\{.*\}", raw, re.S) 抠 JSON 片段再 parse,成功 return (结果, "正则提取");
    #       3) OutputFixingParser.from_llm(parser=parser, llm=llm).parse(raw) 兜底,return (结果, "LLM 修复")
    # 提示: 每层仅在上一层抛 OutputParserException 时才降级;
    #       层名(严格解析/正则提取/LLM 修复)会作为过关路径打进战报,请与上面写法完全一致
    raise NotImplementedError("robust_parse 尚未实现:请按 TODO 提示写三层防线")


def forge(theme: str):
    """铸剑主流程:快路径走重试链,重试耗尽降级到三层防线(慢路径)。"""
    prompt = build_prompt()
    llm = get_llm()
    # TODO: retry_parser = RetryWithErrorOutputParser.from_llm(parser=parser, llm=llm, max_retries=1)
    prompt_value = prompt.format_prompt(theme=theme)
    completion = llm.invoke(prompt_value)  # 只调一次模型,修复的是同一份输出
    # TODO: try return retry_parser.parse_with_prompt(completion, prompt_value), "重试链";
    #       except OutputParserException 时 return robust_parse(completion, llm)
    # 提示: 降级时修的是 completion 这一份坏输出,不要再 invoke 让模型重新答一遍——
    #       retry_parser 内部已经带着报错信息重试过,max_retries 就是给它的预算
    raise NotImplementedError("forge 尚未实现:请按 TODO 提示接上重试链与降级")


def main() -> None:
    """开一炉走完整流水线,再用一段脏输入自检三层防线。"""
    order, route = forge("东海怒涛")
    print("== 铸剑台·出炉战报 ==")
    print(f"  通关路径 : {route}")
    print(f"  剑名     : {order.name}")
    print(f"  主材     : {order.material}")
    print(f"  锋芒     : {order.sharpness}/100")
    print(f"  铭文     : {order.inscription}")
    print("\n== 铸剑台·防线自检(散文包裹的脏输入) ==")
    dirty = '{"name": "照胆", "material": "陨星砂", "sharpness": 95, "inscription": "照胆明心"},请东家过目!'
    fixed, fix_route = robust_parse(dirty, get_llm())
    print(f"  通关路径 : {fix_route}")
    print(f"  修复结果 : {fixed.name} / 锋芒 {fixed.sharpness}/100")


if __name__ == "__main__":
    main()
