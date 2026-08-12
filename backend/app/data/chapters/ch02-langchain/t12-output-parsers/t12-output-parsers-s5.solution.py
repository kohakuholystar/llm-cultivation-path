"""黑糖资料室 · 结构化输出验收 · s5：用 LangChain 完成可验证的学习任务。"""
import os
import re
import sys

from pydantic import BaseModel, Field
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.language_models.fake import FakeListLLM
from langchain_openai import ChatOpenAI

# 联网前置检查:没有 Key 且未开 MOCK 时给出引导并优雅退出
if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

# MOCK 剧情:第一流程回复又啰嗦又有错(质量 999 越界),第二流程才是修好的 JSON
MOCK_RESPONSES = ['模型原始输出:{"name": "晨光", "material": "冷色调素材", "sharpness": 999, "inscription": "让创意被看见"},请检查格式!',
                  '{"name": "晨光", "material": "冷色调素材", "sharpness": 92, "inscription": "让创意被看见"}']


class SwordOrder(BaseModel):
    """一份方案的制作单:黑糖资料室全链路的统一数据契约。"""

    name: str = Field(description="方案名称,两到四个汉字,要有古意")
    material: str = Field(description="主材,如 冷色调图片/品牌字体/活动图标")
    sharpness: int = Field(ge=1, le=100, description="质量评分,1-100 的整数")
    inscription: str = Field(description="方案文案,不超过十二字")


parser = PydanticOutputParser(pydantic_object=SwordOrder)


def ask_for_repair(raw: str, llm) -> SwordOrder:
    """用一次明确、可审计的修复调用处理最后的坏输出。"""
    fixed = llm.invoke(
        "只返回符合下列 JSON Schema 的 JSON，不要解释。\n"
        f"原输出：{raw}\n{parser.get_format_instructions()}"
    )
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
            pass  # 抠出来了但内容违约(如质量 999),继续降级
    # 第三层:LLM 修复——额外调用明确写在应用代码中，便于审计成本。
    return ask_for_repair(raw, llm), "第三层·LLM 修复"


def main() -> None:
    """开一流程,展示三层防线如何接力拦下脏输出。"""
    llm = get_llm()
    raw = llm.invoke("请以「塞北飞雪」为题开一张内容方案单。")
    raw_text = getattr(raw, "content", raw)  # ChatModel 返回 AIMessage，解析器需要纯文本
    print(f"== 原始输出 ==\n{raw_text}\n")
    order, route = robust_parse(raw_text, llm)
    print(f"== 解析成功({route}) ==")
    print(f"  方案名称 : {order.name}")
    print(f"  主材 : {order.material}")
    print(f"  质量 : {order.sharpness}/100")
    print(f"  文案 : {order.inscription}")
    print("  (一层败于散文包裹,二层败于质量越界,三层 LLM 修复通过)")


if __name__ == "__main__":
    main()
