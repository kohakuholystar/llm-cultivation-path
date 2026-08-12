"""社团工具箱 · s3:接入 DeepSeek,让模型亲手掏工具

前两步的工具都是手动调用的。本步把社团工具箱 bind 到 DeepSeek:
模型阅读用户的话,自己决定调用哪件工具、传什么参数(tool_calling);
我们负责执行,并把结果包成 ToolMessage 回传,供模型生成最终答复。

无 API Key 时优雅退出;设 MOCK_LLM=1 可离线用剧本跑通完整流程。
"""
import os
import sys

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ValidationError

MOCK = os.environ.get("MOCK_LLM") == "1"  # 离线演示模式

# 联网前置检查:没有 Key 就给出引导并优雅退出,不让学习者面对 traceback
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[社团工具箱] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地离线演示可设 MOCK_LLM=1,用剧本模拟模型决策)")
    sys.exit(0)


class RefineInput(BaseModel):
    """构建器入参契约。"""

    item_name: str = Field(description="要生成的工具名称")
    quantity: int = Field(gt=0, le=99, description="生成数量,1-99 件")
    unit_cost: float = Field(ge=0, description="单件材料成本(预算点)")
    rarity: str = Field(default="基础", description="品质:基础/标准/高级")


RARITY_BONUS = {"基础": 1.0, "标准": 1.5, "高级": 3.0}


def refine_calc(item_name: str, quantity: int, unit_cost: float, rarity: str = "基础") -> str:
    """估算生成工具的总预算点成本,含品质加成。"""
    total = quantity * unit_cost * RARITY_BONUS.get(rarity, 1.0)
    return f"【构建器】{rarity}·{item_name} x{quantity}:共需 {total:.1f} 预算点"


POUCH_STOCK = [
    {"name": "演示设备", "stock": 12, "rarity": "标准"},
    {"name": "构建器", "stock": 3, "rarity": "基础"},
    {"name": "存储卡", "stock": 1, "rarity": "高级"},
]


class StockQueryInput(BaseModel):
    """库存盘点入参。"""

    keyword: str = Field(description="名称关键词,支持模糊匹配")
    min_stock: int = Field(default=0, ge=0, description="最低库存过滤")
    limit: int = Field(default=5, gt=0, le=20, description="最多返回几条")


def query_stock(keyword: str, min_stock: int = 0, limit: int = 5) -> str:
    """按关键词检索社团工具箱中的工具库存。"""
    hits = [i for i in POUCH_STOCK if keyword in i["name"] and i["stock"] >= min_stock][:limit]
    if not hits:
        return f"【库存】没有找到与「{keyword}」相关的工具"
    lines = [f"  · {i['name']}({i['rarity']}) 库存 {i['stock']}" for i in hits]
    return f"【库存】找到 {len(hits)} 件:\n" + "\n".join(lines)


def build_pouch() -> list[StructuredTool]:
    """组装社团工具箱:构建器 + 库存盘点。"""
    return [
        StructuredTool.from_function(func=refine_calc, name="refine_calc",
                                     description="估算生成工具的总预算点成本", args_schema=RefineInput),
        StructuredTool.from_function(func=query_stock, name="query_stock",
                                     description="按关键词检索社团工具箱中的工具库存", args_schema=StockQueryInput),
    ]


def dispatch(pouch: list[StructuredTool], name: str, arguments: dict) -> str:
    """按名字取工具并执行;任何失败都翻译成文本,绝不向外抛出。"""
    tool = next((t for t in pouch if t.name == name), None)
    if tool is None:
        return f"社团工具箱里没有名为 {name} 的工具"
    try:
        return tool.invoke(arguments)
    except ValidationError as exc:
        err = exc.errors()[0]
        return f"参数校验失败,字段 {err['loc'][0]}: {err['msg']}"


def build_llm() -> ChatOpenAI:
    """装配 DeepSeek 客户端(OpenAI 兼容协议),配置全部来自环境变量。"""
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        temperature=0,  # 工具调用要确定性,关掉随机性
    )


def mock_model_reply() -> AIMessage:
    """离线剧本:假装模型读完用户的话,决定连掏两件工具。"""
    return AIMessage(content="", tool_calls=[
        {"name": "query_stock", "args": {"keyword": "方案"}, "id": "call_1"},
        {"name": "refine_calc", "args": {"item_name": "演示设备", "quantity": 2,
         "unit_cost": 150.0, "rarity": "高级"}, "id": "call_2"},
    ])


def run_agent_turn(user_text: str) -> None:
    """一个完整的 tool_calling 回合:模型挑工具 → 社团工具箱执行 → 结果回传。"""
    pouch = build_pouch()
    if MOCK:
        print("[MOCK] 使用剧本模拟模型决策")
        reply = mock_model_reply()
    else:
        # bind_tools 把每件工具的 JSON Schema 随请求发给模型
        llm = build_llm().bind_tools(pouch)
        reply = llm.invoke([HumanMessage(content=user_text)])

    if not reply.tool_calls:
        print("模型本回合没有调用工具,直接回复:", reply.content)
        return

    print(f"模型决定调用 {len(reply.tool_calls)} 件工具:")
    messages = [HumanMessage(content=user_text), reply]
    for call in reply.tool_calls:
        text = dispatch(pouch, call["name"], call["args"])
        print(f"  ◆ {call['name']} -> {text.splitlines()[0]}")
        # 结果必须包成 ToolMessage,tool_call_id 是结果与调用的配对凭证
        messages.append(ToolMessage(content=text, tool_call_id=call["id"]))

    print(f"\n本回合消息历史共 {len(messages)} 条,ToolMessage 已就绪,")
    print("下一步把 messages 回喂模型,即可生成面向用户的最终答复。")


def main() -> None:
    run_agent_turn("帮我查一下方案类工具的库存,再算生成两个高级演示设备要多少预算点")


if __name__ == "__main__":
    main()
