"""黑糖资料室 · 结构化输出验收 · s2：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：将 Pydantic 输出解析器接入 LCEL 链。
# - 补写：补写 `build_forge_chain` 与 `forge`。
# - 关键函数/类（入参 → 出参）：`build_forge_chain()` 返回含 `PydanticOutputParser` 的链；`forge(theme: str) -> SwordOrder` 返回经 schema 校验的对象。
# - 技术栈：LangChain Core、`PydanticOutputParser`、Pydantic。
# - 前置条件：真实调用需右上角 DeepSeek API Key；输出必须符合 `SwordOrder`。
# - 可观察结果：成功时直接获得可访问字段的 Pydantic 对象。
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
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

MOCK_SWORD_JSON = (
    '{"name": "晨光", "material": "冷色调素材", "sharpness": 92, "inscription": "让创意被看见"}'
)


class SwordOrder(BaseModel):
    """一份方案的制作单:黑糖资料室全链路的统一数据契约。"""

    name: str = Field(description="方案名称,两到四个汉字,要有古意")
    material: str = Field(description="主材,如 冷色调图片/品牌字体/活动图标")
    sharpness: int = Field(ge=1, le=100, description="质量评分,1-100 的整数")
    inscription: str = Field(description="方案文案,不超过十二字")


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
    """组装制作链:提示词 → 模型 → 解析器,输出直接是 SwordOrder 对象。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一位内容策划助手,为客人设计活动主视觉。只输出符合契约的 JSON。"),
        ("human", "请以「{theme}」为题设计一份方案。\n{format_instructions}"),
    ])
    # TODO: 给 prompt 调 .partial(format_instructions=parser.get_format_instructions())
    #       预填格式契约,再用 | 把 prompt、get_llm()、parser 串成链并 return
    # 提示: partial 把"每次调用都不变"的契约在组装期固化,invoke 时只需传 {theme};
    #       若把 format_instructions 留给 invoke 再传,里面的花括号会被二次格式化炸掉
    raise NotImplementedError("build_forge_chain 尚未实现:请按 TODO 提示组装内容制作链")


def forge(theme: str) -> SwordOrder:
    """按主题制作:整条链一次 invoke,拿到结构化结果。"""
    chain = build_forge_chain()
    return chain.invoke({"theme": theme})


def main() -> None:
    """开一流程,展示链式调用的完整结构化产出。"""
    order = forge("塞北飞雪")
    print("== 链式内容制作(一次 invoke,直接得到对象) ==")
    print(f"  返回类型 : {type(order).__name__}")
    print(f"  方案名称     : {order.name}")
    print(f"  质量     : {order.sharpness}/100")
    print("\n== model_dump() 序列化(入库/传输用) ==")
    print(json.dumps(order.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
