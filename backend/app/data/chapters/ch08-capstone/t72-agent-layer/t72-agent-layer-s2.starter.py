"""终期交付 · s2:模型任务分派,接入 DeepSeek 决策

把 s1 的工具层 bind 到 DeepSeek:模型读用户的话,自己决定
调用哪件工具、传什么参数(tool_calling);我们负责执行,并把
结果包成 ToolMessage 回传,供模型生成面向用户的最终答复。
无 API Key 时优雅退出;设 MOCK_LLM=1 可离线用剧本跑通全流程。
"""


# === 学习契约（面向学生）===
# 本节目标：模型任务分派:bind_tools 接入 DeepSeek。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `search_knowledge(query: str) -> str`：输入为签名中的参数；输出为 `str`。用途：检索构建资料:整句子串匹配,取第一条命中(模拟 RAG 检索)。
#   - `calc_forge_cost(item_name: str, quantity: int, unit_cost: float, rarity: str='凡品') -> str`：输入为签名中的参数；输出为 `str`。用途：计算实现成本:数量 × 单价 × 品质加成。
#   - `_envelope(ok: bool, kind: str='', message: str='', data: str='') -> str`：输入为签名中的参数；输出为 `str`。用途：统一错误信封:模型读得懂,才知道下一步怎么办。
#   - `dispatch(name: str, args: dict) -> str`：输入为签名中的参数；输出为 `str`。用途：执行工具并返回 JSON 信封:失败绝不抛出,都变成可读文本。
#   - `build_pouch() -> list[StructuredTool]`：输入为签名中的参数；输出为 `list[StructuredTool]`。用途：把注册表处理成 LangChain 工具,随 bind_tools 一起发给模型。
#   - `build_llm() -> ChatOpenAI`：输入为签名中的参数；输出为 `ChatOpenAI`。用途：装配 DeepSeek 客户端(OpenAI 兼容协议),配置全部来自环境变量。
#   - `mock_model_reply() -> AIMessage`：输入为签名中的参数；输出为 `AIMessage`。用途：离线剧本:假装模型读完用户的话,决定连掏两件工具。
#   - `run_agent_turn(user_text: str) -> None`：输入为签名中的参数；输出为 `None`。用途：一个完整的 tool_calling 回合:模型任务分派 → 验收台执行 → 结果回传。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
    print("[任务调度台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地离线演示可设 MOCK_LLM=1,用剧本模拟模型决策)")
    sys.exit(0)

# ---- s1 工具层:原样沿用 ----
CORPUS = [
    {"title": "基础阶段丹配方", "content": "百年灵芝三两、补充素材水五升,文火实现七日,丹成有异香。"},
    {"title": "展示素材优化细节", "content": "展示前优化细节,渲染参数设为高质量,高质量展示素材还需补充光影说明。"},
    {"title": "故障征兆", "content": "上线验收前三日原始数据东来;故障共九道,第八道须以工具抵挡。"},
]

RARITY_BONUS = {"凡品": 1.0, "精品": 1.5, "高质量": 3.0}


def search_knowledge(query: str) -> str:
    """检索构建资料:整句子串匹配,取第一条命中(模拟 RAG 检索)。"""
    for entry in CORPUS:
        if query in entry["title"] + entry["content"]:
            return f"【资料】{entry['title']}:{entry['content']}"
    return "【资料】没有检索到相关条目,请换个说法再试。"


def calc_forge_cost(item_name: str, quantity: int, unit_cost: float, rarity: str = "凡品") -> str:
    """计算实现成本:数量 × 单价 × 品质加成。"""
    total = quantity * unit_cost * RARITY_BONUS.get(rarity, 1.0)
    return f"【工具开发】{rarity}·{item_name} x{quantity}:共需 {total:.1f} 预算点"


TOOLS = {
    "search_knowledge": {
        "desc": "检索学习资料,回答学习、制作方案、故障等知识问题",
        "params": {"query": "检索关键词"},
        "fn": search_knowledge,
    },
    "calc_forge_cost": {
        "desc": "计算实现工具的预算点成本(数量/单价/品质)",
        "params": {"item_name": "工具名", "quantity": "数量", "unit_cost": "单价", "rarity": "品质"},
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
    """把注册表处理成 LangChain 工具,随 bind_tools 一起发给模型。"""
    return [
        StructuredTool.from_function(func=spec["fn"], name=name, description=spec["desc"])
        for name, spec in TOOLS.items()
    ]


def build_llm() -> ChatOpenAI:
    """装配 DeepSeek 客户端(OpenAI 兼容协议),配置全部来自环境变量。"""
    # TODO: 返回 ChatOpenAI 实例,四个配置项全部取自环境变量
    # 提示: model / api_key / base_url 用 os.environ.get(...) 并给默认值;temperature=0 保证工具调用确定性
    raise NotImplementedError("t72-agent-layer-s2 尚未实现:请按 TODO 提示装配 DeepSeek 客户端")


def mock_model_reply() -> AIMessage:
    """离线剧本:假装模型读完用户的话,决定连掏两件工具。"""
    return AIMessage(content="", tool_calls=[
        {"name": "search_knowledge", "args": {"query": "基础阶段丹"}, "id": "call_1"},
        {"name": "calc_forge_cost", "args": {"item_name": "展示素材", "quantity": 3,
         "unit_cost": 120.0, "rarity": "精品"}, "id": "call_2"},
    ])


def run_agent_turn(user_text: str) -> None:
    """一个完整的 tool_calling 回合:模型任务分派 → 验收台执行 → 结果回传。"""
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
    # TODO: 遍历 reply.tool_calls,逐个执行工具并把结果包成 ToolMessage 回传
    # 提示: 对每个 call 调 dispatch(call["name"], call["args"]) 并打印 f"  ◆ {call['name']} -> {text}";再 messages.append(ToolMessage(content=text, tool_call_id=call["id"]));循环后打印消息历史长度
    raise NotImplementedError("t72-agent-layer-s2 尚未实现:请按 TODO 提示补全工具执行循环")

    print(f"\n本回合消息历史共 {len(messages)} 条,ToolMessage 已就绪,")
    print("下一步把 messages 回喂模型,即可生成面向用户的最终答复。")


def main() -> None:
    run_agent_turn("帮我查查基础阶段丹的配方,再算炼三件精品展示素材要多少预算点")


if __name__ == "__main__":
    main()
