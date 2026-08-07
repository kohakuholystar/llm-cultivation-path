"""渡劫飞升 · s4:Harness 核心循环,决策-执行-观察

s2 只处理「一轮」:一次工具决策、一次回传。真实 Agent 的回合可能
连环调用多次工具——Harness 把「模型决策 → 渡劫台执行 → 观察回传」
收进循环,直到模型给出最终答复或步数用尽(熔断)。
"""
import json
import os
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

SYSTEM_PROMPT = "你是渡劫台的助道者,回答修炼、丹方、炼器问题要简洁、准确、有仙侠味。"

# ---- 工具层:s1 注册表 + 分发器,原样沿用 ----
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
    """统一错误信封:失败也要变成模型可读的反馈。"""
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


class ChatMemory:
    """短期记忆(精简版):只留最近 max_turns 轮,s3 的摘要压缩另述。"""

    def __init__(self, max_turns: int = 5):
        self.max_turns = max_turns
        self.messages: list = []

    def context(self) -> list:
        """记忆的对外窗口:system + 窗口内消息。"""
        return [{"role": "system", "content": SYSTEM_PROMPT}] + self.messages

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        budget = self.max_turns * 2
        if len(self.messages) > budget:
            self.messages = self.messages[-budget:]


class AgentHarness:
    """回合引擎:循环「决策 → 执行 → 观察」,直到终答或步数熔断。"""

    def __init__(self, llm, memory, max_steps: int = 5):
        self.llm = llm
        self.memory = memory
        self.max_steps = max_steps
        self.trace: list = []      # 工具调用记录:(工具名, 参数)
        self.step_count = 0        # 本回合已执行的总步数

    def run(self, user_text: str) -> str:
        """执行一个完整回合:每一步要么是终答,要么是工具调用。"""
        # TODO: 补全决策-执行-观察循环
        # 提示: 提问先入记忆再取上下文;循环内 invoke 拿 decision,无 tool_calls 即终答(入记忆并 return);有工具则逐个 dispatch、记 trace、ToolMessage 回传;循环耗尽返回「已达最大步数,转人工接管。」
        raise NotImplementedError("t72-agent-layer-s4 尚未实现:请按 TODO 提示补全 Harness 核心循环")


class ScriptedLLM:
    """离线剧本模型:invoke 时按顺序吐出剧本里的回复,无 Key 演示与测试用。"""

    def __init__(self, script: list):
        self.script = script  # 引用共享:invoke 的 pop 直接消费调用方剧本

    def invoke(self, messages: list):
        if not self.script:
            raise RuntimeError("剧本已耗尽:调用次数与剧本对不上")
        return AIMessage(**self.script.pop(0))


script = [
    # 第一问:一问一工具,2 次迭代出终答
    {"content": "", "tool_calls": [{"name": "search_knowledge", "args": {"query": "筑基丹"}, "id": "call_1"}]},
    {"content": "筑基丹以九转灵草为引,文火炼足四十九日,配方详见典籍。"},
    # 第二问:连环五问,每步都要工具,5 次迭代后熔断
    {"content": "", "tool_calls": [{"name": "search_knowledge", "args": {"query": "雷劫"}, "id": "call_2"}]},
    {"content": "", "tool_calls": [{"name": "search_knowledge", "args": {"query": "心魔"}, "id": "call_3"}]},
    {"content": "", "tool_calls": [{"name": "search_knowledge", "args": {"query": "灵根"}, "id": "call_4"}]},
    {"content": "", "tool_calls": [{"name": "search_knowledge", "args": {"query": "渡劫"}, "id": "call_5"}]},
    {"content": "", "tool_calls": [{"name": "search_knowledge", "args": {"query": "天劫"}, "id": "call_6"}]},
]

if MOCK:
    llm = ScriptedLLM(script)
else:
    llm = build_llm().bind_tools(build_pouch())

memory = ChatMemory(max_turns=5)
harness = AgentHarness(llm=llm, memory=memory, max_steps=5)


def main() -> None:
    for q in ["筑基丹怎么炼?", "渡劫前要避开哪些劫难?"]:
        print(f"\n—— 道友问: {q}")
        print("渡劫台:", harness.run(q))
    print("\n[检查] 剧本全部消耗:", not script)
    print("[检查] 总步数:", harness.step_count)
    print("[检查] 工具调用次数:", len(harness.trace))
    print("[检查] 熔断文案:", memory.messages[-1]["content"])
    assert harness.step_count == 7 and len(harness.trace) == 6 and not script


if __name__ == "__main__":
    main()
