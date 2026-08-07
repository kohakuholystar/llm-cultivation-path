"""渡劫飞升 · s6:总装验收,行动报告与完整装配

前五关锻好的零件——s1 工具注册表、s2 一轮对话、s3 记忆压缩、
s4 Harness 循环、s5 重试降级——在这一关总装成「渡劫台」。
DujieAgent 是对外门面:道友只见 chat 与 action_report,
内部怎么装配由构造器注入决定,这正是依赖注入的意义。
"""
import json
import os
import sys
import time

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
    """短期记忆(压缩版):窗口只留最近 max_turns 轮,溢出即压进摘要。"""

    def __init__(self, max_turns: int = 2):
        self.max_turns = max_turns
        self.messages: list = []
        self.summary = ""

    def context(self) -> list:
        """记忆的对外窗口:system + 摘要 + 窗口内消息。"""
        ctx = [{"role": "system", "content": SYSTEM_PROMPT}]
        if self.summary:
            ctx.append({"role": "system", "content": f"[摘要] {self.summary}"})
        return ctx + self.messages

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.compress()

    def compress(self) -> None:
        """窗口溢出时,把最旧的用户消息压进摘要,并丢弃整段旧对话。"""
        budget = self.max_turns * 2
        if len(self.messages) <= budget:
            return
        old = self.messages[:-budget]
        chunk = " ".join(m["content"] for m in old if m["role"] == "user")
        self.messages = self.messages[-budget:]
        if chunk:
            self.summary = f"已压缩对话:{chunk}(从略)"


class AgentHarness:
    """回合引擎:循环「决策 → 执行 → 观察」,收尾前压缩记忆。"""

    def __init__(self, llm, memory, max_steps: int = 5):
        self.llm = llm
        self.memory = memory
        self.max_steps = max_steps
        self.trace: list = []      # 工具调用记录:(工具名, 参数)
        self.step_count = 0        # 本回合已执行的总步数

    def run(self, user_text: str) -> str:
        """执行一个完整回合:每一步要么是终答,要么是工具调用。"""
        self.memory.add("user", user_text)
        messages = list(self.memory.context())
        for _ in range(self.max_steps):
            self.step_count += 1
            decision = self.llm.invoke(messages)
            if not decision.tool_calls:
                self.memory.add("assistant", decision.content)
                self.memory.compress()
                return decision.content
            messages.append(decision)
            for call in decision.tool_calls:
                result = dispatch(call["name"], call["args"])
                self.trace.append((call["name"], call["args"]))
                print(f"  ◆ {call['name']} -> {result}")
                messages.append(ToolMessage(content=result, tool_call_id=call["id"]))
        self.memory.add("assistant", "已达最大步数,转人工接管。")
        self.memory.compress()
        return "已达最大步数,转人工接管。"


class DujieAgent:
    """门面:对外只暴露 chat 与 action_report,依赖由构造器注入。"""

    def __init__(self, memory, harness):
        self.memory = memory
        self.harness = harness
        self.turn_count = 0

    def chat(self, user_text: str) -> str:
        """道友发问:记轮次、走 Harness,返回终答。"""
        self.turn_count += 1
        print(f"\n—— 第 {self.turn_count} 轮: {user_text}")
        return self.harness.run(user_text)

    def action_report(self) -> str:
        """输出本次运行的可观测性汇总:轮次、工具调用、记忆规模。"""
        return "\n".join([
            "===== 渡劫台行动报告 =====",
            f"对话轮数: {self.turn_count}",
            f"工具调用: {len(self.harness.trace)} 次",
            f"记忆规模: {len(self.memory.messages)} 条最近消息 + 摘要 {len(self.memory.summary)} 字",
        ])


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
    # 第二问:成本计算工具,同样 2 次迭代
    {"content": "", "tool_calls": [{"name": "calc_forge_cost", "args": {"item_name": "飞剑", "quantity": 3, "unit_cost": 120, "rarity": "精品"}, "id": "call_2"}]},
    {"content": "三件精品飞剑共需 540 灵石,已在账房记下。"},
    # 第三问:纯闲聊,不调任何工具
    {"content": "那太好了,我们继续。"},
]

if MOCK:
    llm = ScriptedLLM(script)
else:
    llm = build_llm().bind_tools(build_pouch())

memory = ChatMemory(max_turns=2)
harness = AgentHarness(llm=llm, memory=memory, max_steps=5)
agent = DujieAgent(memory=memory, harness=harness)


def main() -> None:
    print("—— 渡劫台开张 ——")
    print("道友: 筑基丹怎么炼?")
    print("渡劫台:", agent.chat("筑基丹怎么炼?"))
    print("道友: 三件精品飞剑多少钱?")
    print("渡劫台:", agent.chat("三件精品飞剑多少钱?"))
    print("道友: 好,我们继续。")
    print("渡劫台:", agent.chat("好,我们继续。"))
    print()
    print(agent.action_report())
    print("\n[检查] 剧本全部消耗:", not script)
    print("[检查] 摘要已生成:", bool(agent.memory.summary))
    print("[检查] 摘要内容:", agent.memory.summary)
    print("[检查] 窗口剩余:", len(agent.memory.messages))
    assert not script
    assert bool(agent.memory.summary)
    assert "筑基丹怎么炼?" in agent.memory.summary
    assert len(agent.memory.messages) == 4  # max_turns=2 → 预算 4 条


if __name__ == "__main__":
    main()
