"""百宝囊 · s3:接入 DeepSeek,让模型亲手掏法宝

前两步的法宝都是手动调用的。本步把百宝囊 bind 到 DeepSeek:
模型阅读用户的话,自己决定调用哪件法宝、传什么参数(tool_calling);
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
    print("[百宝囊] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地离线演示可设 MOCK_LLM=1,用剧本模拟模型决策)")
    sys.exit(0)


class RefineInput(BaseModel):
    """炼器炉入参契约。"""

    item_name: str = Field(description="要炼制的法器名称")
    quantity: int = Field(gt=0, le=99, description="炼制数量,1-99 件")
    unit_cost: float = Field(ge=0, description="单件材料成本(灵石)")
    rarity: str = Field(default="凡品", description="品质:凡品/精品/仙品")


RARITY_BONUS = {"凡品": 1.0, "精品": 1.5, "仙品": 3.0}


def refine_calc(item_name: str, quantity: int, unit_cost: float, rarity: str = "凡品") -> str:
    """估算炼制法器的总灵石成本,含品质加成。"""
    total = quantity * unit_cost * RARITY_BONUS.get(rarity, 1.0)
    return f"【炼器炉】{rarity}·{item_name} x{quantity}:共需 {total:.1f} 灵石"


POUCH_STOCK = [
    {"name": "飞剑", "stock": 12, "rarity": "精品"},
    {"name": "丹炉", "stock": 3, "rarity": "凡品"},
    {"name": "储物戒", "stock": 1, "rarity": "仙品"},
]


class StockQueryInput(BaseModel):
    """库存盘点入参。"""

    keyword: str = Field(description="名称关键词,支持模糊匹配")
    min_stock: int = Field(default=0, ge=0, description="最低库存过滤")
    limit: int = Field(default=5, gt=0, le=20, description="最多返回几条")


def query_stock(keyword: str, min_stock: int = 0, limit: int = 5) -> str:
    """按关键词检索百宝囊中的法器库存。"""
    hits = [i for i in POUCH_STOCK if keyword in i["name"] and i["stock"] >= min_stock][:limit]
    if not hits:
        return f"【库存】没有找到与「{keyword}」相关的法器"
    lines = [f"  · {i['name']}({i['rarity']}) 库存 {i['stock']}" for i in hits]
    return f"【库存】找到 {len(hits)} 件:\n" + "\n".join(lines)


def build_pouch() -> list[StructuredTool]:
    """锻造百宝囊:炼器炉 + 库存盘点。"""
    return [
        StructuredTool.from_function(func=refine_calc, name="refine_calc",
                                     description="估算炼制法器的总灵石成本", args_schema=RefineInput),
        StructuredTool.from_function(func=query_stock, name="query_stock",
                                     description="按关键词检索百宝囊中的法器库存", args_schema=StockQueryInput),
    ]


def dispatch(pouch: list[StructuredTool], name: str, arguments: dict) -> str:
    """按名字取法宝并执行;任何失败都翻译成文本,绝不向外抛出。"""
    tool = next((t for t in pouch if t.name == name), None)
    if tool is None:
        return f"百宝囊里没有名为 {name} 的法宝"
    try:
        return tool.invoke(arguments)
    except ValidationError as exc:
        err = exc.errors()[0]
        return f"参数校验失败,字段 {err['loc'][0]}: {err['msg']}"


def build_llm() -> ChatOpenAI:
    """装配 DeepSeek 客户端(OpenAI 兼容协议),配置全部来自环境变量。"""
    # TODO: 返回配置齐全的 ChatOpenAI 实例
    # 提示: ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"), api_key=os.environ.get("OPENAI_API_KEY"), base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"), temperature=0)
    raise NotImplementedError("t33-s3 尚未实现:请按 TODO 提示装配 ChatOpenAI 客户端")


def mock_model_reply() -> AIMessage:
    """离线剧本:假装模型读完用户的话,决定连掏两件法宝。"""
    return AIMessage(content="", tool_calls=[
        {"name": "query_stock", "args": {"keyword": "剑"}, "id": "call_1"},
        {"name": "refine_calc", "args": {"item_name": "飞剑", "quantity": 2,
         "unit_cost": 150.0, "rarity": "仙品"}, "id": "call_2"},
    ])


def run_agent_turn(user_text: str) -> None:
    """一个完整的 tool_calling 回合:模型挑法宝 → 百宝囊执行 → 结果回传。"""
    pouch = build_pouch()
    if MOCK:
        print("[MOCK] 使用剧本模拟模型决策")
        reply = mock_model_reply()
    else:
        # bind_tools 把每件法宝的 JSON Schema 随请求发给模型
        llm = build_llm().bind_tools(pouch)
        reply = llm.invoke([HumanMessage(content=user_text)])

    # TODO: 判空后逐个执行法宝调用,把结果包成 ToolMessage 回传
    # 提示: if not reply.tool_calls: 打印并 return;否则 for call in reply.tool_calls:
    #       text = dispatch(pouch, call["name"], call["args"]) 并打印首行;
    #       messages.append(ToolMessage(content=text, tool_call_id=call["id"]));最后打印消息历史长度
    raise NotImplementedError("t33-s3 尚未实现:请按 TODO 提示补全 tool_calling 回合逻辑")


def main() -> None:
    run_agent_turn("帮我查一下剑类法器的库存,再算炼两把仙品飞剑要多少灵石")


if __name__ == "__main__":
    main()
