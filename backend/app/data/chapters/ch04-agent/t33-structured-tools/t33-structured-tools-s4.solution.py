"""社团工具箱 · s4:异步工具与并发处理

在 s3 的 tool_calling 回合之上,为社团工具箱添置两件异步工具:
「鉴定」appraise 与「询价」scout_price——它们模拟耗时的远程服务。
当模型一个回合要求连掏多件工具时,用 ainvoke + asyncio.gather 并发执行,
把串行等待变成一次齐发,并对比两种执行方式的耗时。

无 API Key 时优雅退出;设 MOCK_LLM=1 可离线跑通完整流程。
"""
import asyncio
import os
import sys
import time

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ValidationError

MOCK = os.environ.get("MOCK_LLM") == "1"  # 离线演示模式

# 联网前置检查:没有 Key 就给出引导并优雅退出
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[社团工具箱] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地离线演示可设 MOCK_LLM=1,用剧本模拟模型决策)")
    sys.exit(0)


class RefineInput(BaseModel):
    """构建器入参契约(s1 的同步工具,继续随囊携带)。"""

    item_name: str = Field(description="要生成的工具名称")
    quantity: int = Field(gt=0, le=99, description="生成数量,1-99 件")
    unit_cost: float = Field(ge=0, description="单件材料成本(预算点)")
    rarity: str = Field(default="基础", description="品质:基础/标准/高级")


RARITY_BONUS = {"基础": 1.0, "标准": 1.5, "高级": 3.0}


def refine_calc(item_name: str, quantity: int, unit_cost: float, rarity: str = "基础") -> str:
    """估算生成工具的总预算点成本,含品质加成。"""
    total = quantity * unit_cost * RARITY_BONUS.get(rarity, 1.0)
    return f"【构建器】{rarity}·{item_name} x{quantity}:共需 {total:.1f} 预算点"


class AppraiseInput(BaseModel):
    """鉴定入参:depth 越深耗时越久。"""

    item_name: str = Field(description="要鉴定的工具名称")
    depth: int = Field(default=1, ge=1, le=3, description="鉴定深度 1-3")


class ScoutInput(BaseModel):
    """询价入参。"""

    item_name: str = Field(description="要询价的工具名称")


async def appraise(item_name: str, depth: int = 1) -> str:
    """异步鉴定工具:模拟耗时的远程鉴定服务(真实场景这里是网络 I/O)。"""
    await asyncio.sleep(0.2 * depth)
    return f"【鉴定】{item_name}:深度 {depth},灵性充沛,可放心生成"


async def scout_price(item_name: str) -> str:
    """异步询价:模拟跨坊市询价的远程调用。"""
    await asyncio.sleep(0.3)
    return f"【询价】{item_name}:坊市均价 150 预算点,近日行情平稳"


def build_pouch() -> list[StructuredTool]:
    """社团工具箱全员:同步工具用 func=,异步工具必须用 coroutine= 注册。"""
    return [
        StructuredTool.from_function(func=refine_calc, name="refine_calc",
                                     description="估算生成工具的总预算点成本", args_schema=RefineInput),
        StructuredTool.from_function(coroutine=appraise, name="appraise",
                                     description="鉴定工具灵性,depth 1-3", args_schema=AppraiseInput),
        StructuredTool.from_function(coroutine=scout_price, name="scout_price",
                                     description="查询工具坊市均价", args_schema=ScoutInput),
    ]


def build_llm() -> ChatOpenAI:
    """装配 DeepSeek 客户端(OpenAI 兼容协议)。"""
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        temperature=0,
    )


def mock_model_reply() -> AIMessage:
    """离线剧本:模型一个回合连掏三件工具(一次深度鉴定 + 浅鉴定 + 询价)。"""
    return AIMessage(content="", tool_calls=[
        {"name": "appraise", "args": {"item_name": "演示设备", "depth": 2}, "id": "call_1"},
        {"name": "appraise", "args": {"item_name": "存储卡", "depth": 1}, "id": "call_2"},
        {"name": "scout_price", "args": {"item_name": "演示设备"}, "id": "call_3"},
    ])


async def call_one(pouch: list[StructuredTool], call: dict) -> tuple[dict, str]:
    """执行单次工具调用:按 tool.coroutine 分流同步/异步通道。"""
    tool = next((t for t in pouch if t.name == call["name"]), None)
    if tool is None:
        return call, f"社团工具箱里没有名为 {call['name']} 的工具"
    try:
        if tool.coroutine is not None:
            # 异步工具:真正 await,等待期间事件循环可以调度别的工具
            return call, await tool.ainvoke(call["args"])
        # 同步工具:直接调用(生产环境应 run_in_executor 丢线程池,避免阻塞事件循环)
        return call, tool.invoke(call["args"])
    except ValidationError as exc:
        return call, f"参数校验失败,字段 {exc.errors()[0]['loc'][0]}: {exc.errors()[0]['msg']}"


async def run_agent_turn(user_text: str) -> None:
    """tool_calling 回合(异步版):模型连掏多件工具,我们并发处理。"""
    pouch = build_pouch()
    if MOCK:
        print("[MOCK] 使用剧本模拟模型决策")
        reply = mock_model_reply()
    else:
        llm = build_llm().bind_tools(pouch)
        reply = llm.invoke([HumanMessage(content=user_text)])

    if not reply.tool_calls:
        print("模型本回合没有调用工具,直接回复:", reply.content)
        return
    calls = reply.tool_calls
    print(f"模型决定调用 {len(calls)} 件工具,分别演示串行与并发执行:")

    # 串行基线:逐个 await,耗时是各工具之和
    t0 = time.perf_counter()
    for c in calls:
        await call_one(pouch, c)
    t_serial = time.perf_counter() - t0

    # 并发处理:asyncio.gather 一次齐发,耗时约等于最慢的一件
    t0 = time.perf_counter()
    results = await asyncio.gather(*(call_one(pouch, c) for c in calls))
    t_parallel = time.perf_counter() - t0

    messages = [HumanMessage(content=user_text), reply]
    for call, text in results:
        print(f"  ◆ {call['name']} -> {text}")
        messages.append(ToolMessage(content=text, tool_call_id=call["id"]))
    print(f"\n串行耗时 {t_serial:.2f}s,并发耗时 {t_parallel:.2f}s")
    print(f"消息历史共 {len(messages)} 条,ToolMessage 已就绪,可回喂模型。")


def main() -> None:
    asyncio.run(run_agent_turn("帮我鉴定演示设备和存储卡,再查查演示设备的坊市行情"))


if __name__ == "__main__":
    main()
