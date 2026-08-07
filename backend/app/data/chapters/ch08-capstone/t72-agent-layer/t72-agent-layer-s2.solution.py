"""渡劫飞升 · s2:模型点将,接入 DeepSeek 决策

把 s1 的工具层 bind 到 DeepSeek:模型读用户的话,自己决定
调用哪件工具、传什么参数(tool_calling);我们负责执行,并把
结果包成 ToolMessage 回传,供模型生成面向用户的最终答复。
无 API Key 时优雅退出;设 MOCK_LLM=1 可离线用剧本跑通全流程。
"""
import json
import os
import re
import sys

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

MOCK = os.environ.get("MOCK_LLM") == "1"  # 离线演示模式

# 联网前置检查:没有 Key 就给出引导并优雅退出,不让学习者面对 traceback
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[渡劫台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地离线演示可设 MOCK_LLM=1,用剧本模拟模型决策)")
    sys.exit(0)

# ---- s1 工具层:原样沿用 ----
CORPUS = [
    {"title": "筑基丹配方", "content": "百年灵芝三两、灵泉水五升,文火炼制七日,丹成有异香。"},
    {"title": "飞剑淬火", "content": "辰时淬火,炉温三千度,仙品飞剑还需加注灵泉。"},
    {"title": "雷劫征兆", "content": "渡劫前三日紫气东来;雷劫共九道,第八道须以法宝抵挡。"},
]

RARITY_BONUS = {"凡品": 1.0, "精品": 1.5, "仙品": 3.0}


def search_knowledge(query: str) -> str:
    """检索修炼典籍:整句子串匹配,取第一条命中(模拟 RAG 检索)。"""
    for entry in CORPUS:
        if query in entry["title"] + entry["content"]:
            return f"【典籍】{entry['title']}:{entry['content']}"
    return "【典籍】没有检索到相关条目,请换个说法再试。"


def calc_forge_cost(item_name: str, quantity: int, unit_cost: float, rarity: str = "凡品") -> str:
    """计算炼制成本:数量 × 单价 × 品质加成。"""
    total = quantity * unit_cost * RARITY_BONUS.get(rarity, 1.0)
    return f"【炼器】{rarity}·{item_name} x{quantity}:共需 {total:.1f} 灵石"


TOOLS = {
    "search_knowledge": {
        "desc": "检索修炼典籍,回答修行、丹方、雷劫等知识问题",
        "params": {"query": "检索关键词"},
        "fn": search_knowledge,
    },
    "calc_forge_cost": {
        "desc": "计算炼制法器的灵石成本(数量/单价/品质)",
        "params": {"item_name": "法器名", "quantity": "数量", "unit_cost": "单价", "rarity": "品质"},
        "fn": calc_forge_cost,
    },
}


def _envelope(ok: bool, kind: str = "", message: str = "", data: str = "") -> str:
    """统一错误信封:模型读得懂,才知道下一步怎么办。"""
    if ok:
        return json.dumps({"ok": True, "data": data}, ensure_ascii=False)
    return json.dumps({"ok": False, "error": {"type": kind, "message": message}}, ensure_ascii=False)


def dispatch(name: str, args: dict) -> str:
    """执行工具并返回 JSON 信封:失败绝不抛出,都变成可读文本。"""
    spec = TOOLS.get(name)
    if spec is None:
        return _envelope(False, "unknown_tool", f"没有名为 {name} 的工具")
    missing = [k for k in spec["params"] if k not in args]
    if missing:
        return _envelope(False, "invalid_args", f"缺少参数: {missing}")
    try:
        return _envelope(True, data=spec["fn"](**args))
    except Exception as exc:  # noqa: BLE001
        return _envelope(False, "internal_error", f"{type(exc).__name__}: {exc}")


def build_pouch() -> list[StructuredTool]:
    """把注册表锻造成 LangChain 工具,随 bind_tools 一起发给模型。"""
    return [
        StructuredTool.from_function(func=spec["fn"], name=name, description=spec["desc"])
        for name, spec in TOOLS.items()
    ]


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
        {"name": "search_knowledge", "args": {"query": "筑基丹"}, "id": "call_1"},
        {"name": "calc_forge_cost", "args": {"item_name": "飞剑", "quantity": 3,
         "unit_cost": 120.0, "rarity": "精品"}, "id": "call_2"},
    ])


def run_agent_turn(user_text: str) -> None:
    """一个完整的 tool_calling 回合:模型点将 → 渡劫台执行 → 结果回传。"""
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

    print(f"模型决定调用 {len(reply.tool_calls)} 件工具:")
    messages = [HumanMessage(content=user_text), reply]
    for call in reply.tool_calls:
        text = dispatch(call["name"], call["args"])
        print(f"  ◆ {call['name']} -> {text}")
        # 结果必须包成 ToolMessage,tool_call_id 是结果与调用的配对凭证
        messages.append(ToolMessage(content=text, tool_call_id=call["id"]))

    print(f"\n本回合消息历史共 {len(messages)} 条,ToolMessage 已就绪,")
    print("下一步把 messages 回喂模型,即可生成面向用户的最终答复。")


def main() -> None:
    run_agent_turn("帮我查查筑基丹的配方,再算炼三件精品飞剑要多少灵石")


if __name__ == "__main__":
    main()
