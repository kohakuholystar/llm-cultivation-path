"""百宝囊 · s5:异常规范化,给百宝囊装上护符

在 s4 的异步并发回合之上,补齐工程级 Agent 的最后一块短板:错误处理。
炼器炉新增业务约束(仙品一次最多炼 5 件,超出抛 ToolException);
调度层新增 safe_call:无论参数校验失败、业务异常还是未知错误,
都收敛成统一 JSON 信封作为 ToolMessage 回传——模型才有机会自我修正。

无 API Key 时优雅退出;设 MOCK_LLM=1 可离线跑通完整流程。
"""
import asyncio
import json
import os
import sys

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool, ToolException
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
    """炼器炉入参契约。"""

    item_name: str = Field(description="要炼制的法器名称")
    quantity: int = Field(gt=0, le=99, description="炼制数量,1-99 件")
    unit_cost: float = Field(ge=0, description="单件材料成本(灵石)")
    rarity: str = Field(default="凡品", description="品质:凡品/精品/仙品")


RARITY_BONUS = {"凡品": 1.0, "精品": 1.5, "仙品": 3.0}


def refine_calc(item_name: str, quantity: int, unit_cost: float, rarity: str = "凡品") -> str:
    """估算炼制法器的总灵石成本,含品质加成。仙品一次最多炼 5 件。"""
    if rarity == "仙品" and quantity > 5:
        # 业务约束失败:主动抛 ToolException,表示"合情合理地失败"
        raise ToolException(f"炉火不足:仙品法器一次最多炼 5 件(收到 {quantity} 件)")
    total = quantity * unit_cost * RARITY_BONUS.get(rarity, 1.0)
    return f"【炼器炉】{rarity}·{item_name} x{quantity}:共需 {total:.1f} 灵石"


class AppraiseInput(BaseModel):
    """鉴定入参。"""

    item_name: str = Field(description="要鉴定的法器名称")
    depth: int = Field(default=1, ge=1, le=3, description="鉴定深度 1-3")


async def appraise(item_name: str, depth: int = 1) -> str:
    """异步鉴定法器:模拟耗时的远程鉴定服务。"""
    await asyncio.sleep(0.2 * depth)
    return f"【鉴定】{item_name}:深度 {depth},灵性充沛,可放心炼制"


def build_pouch() -> list[StructuredTool]:
    """百宝囊:同步法宝用 func=,异步法宝用 coroutine=。"""
    return [
        StructuredTool.from_function(func=refine_calc, name="refine_calc",
                                     description="估算炼制法器的总灵石成本", args_schema=RefineInput),
        StructuredTool.from_function(coroutine=appraise, name="appraise",
                                     description="鉴定法器灵性,depth 1-3", args_schema=AppraiseInput),
    ]


def build_llm() -> ChatOpenAI:
    """装配 DeepSeek 客户端(OpenAI 兼容协议)。"""
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        temperature=0,
    )


def _err(kind: str, message: str, retryable: bool) -> str:
    """生成统一错误信封:模型读得懂,才知道下一步怎么办。"""
    envelope = {"ok": False, "error": {"type": kind, "message": message, "retryable": retryable}}
    return json.dumps(envelope, ensure_ascii=False)


async def safe_call(pouch: list[StructuredTool], call: dict) -> str:
    """执行法宝并永远返回规范化 JSON 信封——绝不让异常逃出百宝囊。"""
    tool = next((t for t in pouch if t.name == call["name"]), None)
    if tool is None:
        return _err("unknown_tool", f"百宝囊里没有名为 {call['name']} 的法宝", retryable=False)
    try:
        if tool.coroutine is not None:
            result = await tool.ainvoke(call["args"])
        else:
            result = tool.invoke(call["args"])
        return json.dumps({"ok": True, "data": result}, ensure_ascii=False)
    except ValidationError as exc:
        # 参数校验错误发生在进入函数体之前,handle_tool_error 兜不住,必须在调度层捕获
        err = exc.errors()[0]
        return _err("invalid_args", f"字段 {err['loc'][0]}: {err['msg']}", retryable=True)
    except ToolException as exc:
        # 业务异常:调用合情合理地失败,模型换个参数通常能成
        return _err("tool_error", str(exc), retryable=True)
    except Exception as exc:  # noqa: BLE001 —— 兜底:未知异常也要变成模型可读的反馈
        return _err("internal_error", f"{type(exc).__name__}: {exc}", retryable=False)


def mock_model_reply() -> AIMessage:
    """离线剧本:三件法宝——一次业务失败、一次参数非法、一次正常。"""
    return AIMessage(content="", tool_calls=[
        {"name": "refine_calc", "args": {"item_name": "飞剑", "quantity": 9,
         "unit_cost": 150.0, "rarity": "仙品"}, "id": "call_1"},
        {"name": "appraise", "args": {"item_name": "飞剑", "depth": 9}, "id": "call_2"},
        {"name": "appraise", "args": {"item_name": "储物戒", "depth": 1}, "id": "call_3"},
    ])


async def run_agent_turn(user_text: str) -> None:
    """tool_calling 回合(护符版):任何法宝失败,回合都不中断。"""
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
    print(f"模型决定调用 {len(calls)} 件法宝,全部经过 safe_call 护符:")

    envelopes = await asyncio.gather(*(safe_call(pouch, c) for c in calls))
    ok_count = 0
    messages = [HumanMessage(content=user_text), reply]
    for call, envelope in zip(calls, envelopes):
        ok_count += json.loads(envelope)["ok"]
        print(f"  ◆ {call['name']} -> {envelope}")
        # 无论成败,信封都作为 ToolMessage 回传,模型据此决定重试或放弃
        messages.append(ToolMessage(content=envelope, tool_call_id=call["id"]))

    print(f"\n回合结束:成功 {ok_count} 件,失败 {len(calls) - ok_count} 件,回合未中断。")
    print("失败信封已随消息历史备好,回喂模型即可让它修正参数重试。")


def main() -> None:
    asyncio.run(run_agent_turn("帮我炼九把仙品飞剑,再深度鉴定一下,顺带看看储物戒"))


if __name__ == "__main__":
    main()
