"""黑糖资料室 · 结构化输出验收 · s6：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：将生成、解析、修复组成一条可复用的结构化交付链。
# - 补写：补写 prompt、解析修复和 `forge`。
# - 关键函数/类（入参 → 出参）：`build_prompt()` 创建约束；`robust_parse(raw, llm) -> SwordOrder` 处理解析；`forge(theme: str) -> SwordOrder` 返回最终对象。
# - 技术栈：LangChain LCEL、Pydantic、错误恢复。
# - 前置条件：真实调用需右上角 DeepSeek API Key。
# - 可观察结果：一项主题输入最终交付受 schema 约束的数据对象。
import os
import re
import sys

from pydantic import BaseModel, Field
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.fake import FakeListLLM
from langchain_openai import ChatOpenAI

# 联网前置检查:没有 Key 且未开 MOCK 时给出引导并优雅退出
if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

# MOCK 剧情:第一流程散文废料,重试后第二流程出合规 JSON
MOCK_RESPONSES = [
    "这柄方案唤作龙吟,品牌字体打造,锋利得很!",
    '{"name": "龙吟", "material": "品牌字体", "sharpness": 88, "inscription": "龙吟四海"}',
]


class SwordOrder(BaseModel):
    """一份方案的制作单:黑糖资料室全链路的统一数据契约。"""

    name: str = Field(description="方案名称,两到四个汉字,要有古意")
    material: str = Field(description="主材,如 冷色调图片/品牌字体/活动图标")
    sharpness: int = Field(ge=1, le=100, description="质量评分,1-100 的整数")
    inscription: str = Field(description="方案文案,不超过十二字")


parser = PydanticOutputParser(pydantic_object=SwordOrder)


def ask_for_repair(raw, error: Exception | None, llm) -> SwordOrder:
    """明确发起一次修复请求，让学生看得见额外调用的输入和成本。"""
    text = getattr(raw, "content", raw)
    error_note = f"解析错误：{error}\n" if error else ""
    fixed = llm.invoke(
        "只返回符合下列 JSON Schema 的 JSON，不要解释。\n"
        f"{error_note}原输出：{text}\n{parser.get_format_instructions()}"
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


def build_prompt():
    """制作提示词:契约在组装期用 partial 固化。"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", "你是一位内容策划助手,为客人设计活动主视觉。只输出符合契约的 JSON。"),
            ("human", "请以「{theme}」为题设计一份方案。\n{format_instructions}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())


def robust_parse(raw: str, llm):
    """三层防线(终版兜底):严格解析 → 正则提取 → LLM 修复。"""
    # TODO: 照 s5 写三层防线并返回 (结果, 通关层名):
    #       1) try parser.parse(raw),成功 return (结果, "严格解析");
    #       2) re.search(r"\{.*\}", raw, re.S) 抠 JSON 片段再 parse,成功 return (结果, "正则提取");
    #       3) ask_for_repair(raw, None, llm) 兜底,return (结果, "LLM 修复")
    # 提示: 每层仅在上一层抛 OutputParserException 时才降级;
    #       层名(严格解析/正则提取/LLM 修复)会作为过关路径打进战报,请与上面写法完全一致
    raise NotImplementedError("robust_parse 尚未实现:请按 TODO 提示写三层防线")


def forge(theme: str):
    """制作主流程:快路径走重试链,重试耗尽降级到三层防线(慢路径)。"""
    prompt = build_prompt()
    llm = get_llm()
    prompt_value = prompt.format_prompt(theme=theme)
    completion = llm.invoke(prompt_value)  # 只调一次模型,修复的是同一份输出
    # TODO: 先 return parser.parse(completion), "严格解析";捕获 OutputParserException 后，
    #       先试 return ask_for_repair(completion, error, llm), "显式回流程修复"，再失败才 return robust_parse(completion, llm)。
    # 提示: 修复的是 completion 这一份坏输出；不要另起一流程。第二次修复失败时才进入三层慢路径。
    raise NotImplementedError("forge 尚未实现:请按 TODO 提示接上显式修复与降级")


def main() -> None:
    """开一流程走完整流水线,再用一段脏输入自检三层防线。"""
    order, route = forge("东海怒涛")
    print("== 提示词工作台·出运行报告 ==")
    print(f"  通关路径 : {route}")
    print(f"  方案名称     : {order.name}")
    print(f"  主材     : {order.material}")
    print(f"  质量     : {order.sharpness}/100")
    print(f"  文案     : {order.inscription}")
    print("\n== 提示词工作台·防线自检(散文包裹的脏输入) ==")
    dirty = '{"name": "照胆", "material": "活动图标", "sharpness": 95, "inscription": "照胆明心"},请东家过目!'
    fixed, fix_route = robust_parse(dirty, get_llm())
    print(f"  通关路径 : {fix_route}")
    print(f"  修复结果 : {fixed.name} / 质量 {fixed.sharpness}/100")


if __name__ == "__main__":
    main()
