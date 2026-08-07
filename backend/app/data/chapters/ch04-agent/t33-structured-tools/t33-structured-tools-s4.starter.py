"""百宝囊 · s4:异步法宝与并发淬炼

在 s3 的 tool_calling 回合之上,为百宝囊添置两件异步法宝:
「鉴定」appraise 与「询价」scout_price——它们模拟耗时的远程服务。
当模型一个回合要求连掏多件法宝时,用 ainvoke + asyncio.gather 并发执行,
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
    print("[百宝囊] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地离线演示可设 MOCK_LLM=1,用剧本模拟模型决策)")
    sys.exit(0)


class RefineInput(BaseModel):
    """炼器炉入参契约(s1 的同步法宝,继续随囊携带)。"""

    item_name: str = Field(description="要炼制的法器名称")
    quantity: int = Field(gt=0, le=99, description="炼制数量,1-99 件")
    unit_cost: float = Field(ge=0, description="单件材料成本(灵石)")
    rarity: str = Field(default="凡品", description="品质:凡品/精品/仙品")


RARITY_BONUS = {"凡品": 1.0, "精品": 1.5, "仙品": 3.0}


def refine_calc(item_name: str, quantity: int, unit_cost: float, rarity: str = "凡品") -> str:
    """估算炼制法器的总灵石成本,含品质加成。"""
    total = quantity * unit_cost * RARITY_BONUS.get(rarity, 1.0)
    return f"【炼器炉】{rarity}·{item_name} x{quantity}:共需 {total:.1f} 灵石"


class AppraiseInput(BaseModel):
    """鉴定入参:depth 越深耗时越久。"""

    item_name: str = Field(description="要鉴定的法器名称")
    depth: int = Field(default=1, ge=1, le=3, description="鉴定深度 1-3")


class ScoutInput(BaseModel):
    """询价入参。"""

    item_name: str = Field(description="要询价的法器名称")


async def appraise(item_name: str, depth: int = 1) -> str:
    """异步鉴定法器:模拟耗时的远程鉴定服务(真实场景这里是网络 I/O)。"""
    await asyncio.sleep(0.2 * depth)
    return f"【鉴定】{item_name}:深度 {depth},灵性充沛,可放心炼制"


async def scout_price(item_name: str) -> str:
    """异步询价:模拟跨坊市询价的远程调用。"""
    await asyncio.sleep(0.3)
    return f"【询价】{item_name}:坊市均价 150 灵石,近日行情平稳"


def build_pouch() -> list[StructuredTool]:
    """百宝囊全员:同步法宝用 func=,异步法宝必须用 coroutine= 注册。"""
    # TODO: 注册两件异步法宝 appraise 与 scout_price,与 refine_calc 一起放进列表返回
    # 提示: StructuredTool.from_function(coroutine=appraise, name="appraise", description="鉴定法器灵性,depth 1-3", args_schema=AppraiseInput);scout_price 同理
    raise NotImplementedError("t33-s4 尚未实现:请按 TODO 提示注册两件异步法宝")
    return [
        StructuredTool.from_function(func=refine_calc, name="refine_calc",
                                     description="估算炼制法器的总灵石成本", args_schema=RefineInput),
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
    """离线剧本:模型一个回合连掏三件法宝(一次深度鉴定 + 浅鉴定 + 询价)。"""
    return AIMessage(content="", tool_calls=[
        {"name": "appraise", "args": {"item_name": "飞剑", "depth": 2}, "id": "call_1"},
        {"name": "appraise", "args": {"item_name": "储物戒", "depth": 1}, "id": "call_2"},
        {"name": "scout_price", "args": {"item_name": "飞剑"}, "id": "call_3"},
    ])


async def call_one(pouch: list[StructuredTool], call: dict) -> tuple[dict, str]:
    """执行单次法宝调用:按 tool.coroutine 分流同步/异步通道。"""
    tool = next((t for t in pouch if t.name == call["name"]), None)
    if tool is None:
        return call, f"百宝囊里没有名为 {call['name']} 的法宝"
    try:
        if tool.coroutine is not None:
            # 异步法宝:真正 await,等待期间事件循环可以调度别的法宝
            return call, await tool.ainvoke(call["args"])
        # 同步法宝:直接调用(生产环境应 run_in_executor 丢线程池,避免阻塞事件循环)
        return call, tool.invoke(call["args"])
    except ValidationError as exc:
        return call, f"参数校验失败,字段 {exc.errors()[0]['loc'][0]}: {exc.errors()[0]['msg']}"


async def run_agent_turn(user_text: str) -> None:
    """tool_calling 回合(异步版):模型连掏多件法宝,我们并发淬炼。"""
    pouch = build_pouch()
    if MOCK:
        print("[MOCK] 使用剧本模拟模型决策")
        reply = mock_model_reply()
    else:
        llm = build_llm().bind_tools(pouch)
        reply = llm.invoke([HumanMessage(content=user_text)])

    if not reply.tool_calls:
        print("模型本回合没有调用法宝,直接回复:", reply.content)
        return
    calls = reply.tool_calls
    print(f"模型决定调用 {len(calls)} 件法宝,分别演示串行与并发执行:")

    # 串行基线:逐个 await,耗时是各法宝之和
    t0 = time.perf_counter()
    for c in calls:
        await call_one(pouch, c)
    t_serial = time.perf_counter() - t0

    # TODO: 并发淬炼——asyncio.gather 一次齐发,并对比两种执行方式的耗时
    # 提示: t0 = time.perf_counter();results = await asyncio.gather(*(call_one(pouch, c) for c in calls));
    #       t_parallel = time.perf_counter() - t0;遍历 results 打印每件法宝结果并 append 对应 ToolMessage;
    #       最后打印串行/并发耗时与消息历史长度
    raise NotImplementedError("t33-s4 尚未实现:请按 TODO 提示补上并发淬炼段")


def main() -> None:
    asyncio.run(run_agent_turn("帮我鉴定飞剑和储物戒,再查查飞剑的坊市行情"))


if __name__ == "__main__":
    main()
