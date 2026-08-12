"""终期交付 · s6:总装验收,行动报告与完整装配

前五关锻好的零件——s1 工具注册表、s2 一轮对话、s3 记忆压缩、
s4 Harness 循环、s5 重试降级——在这一关总装成「验收台」。
DujieAgent 是对外门面:协作者只见 chat 与 action_report,
内部怎么装配由构造器注入决定,这正是依赖注入的意义。
"""


# === 学习契约（面向学生）===
# 本节目标：总装验收:行动报告与完整装配。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `search_knowledge(query: str) -> str`：输入为签名中的参数；输出为 `str`。用途：检索构建资料:整句子串匹配,取第一条命中(模拟 RAG 检索)。
#   - `calc_forge_cost(item_name: str, quantity: int, unit_cost: float, rarity: str='凡品') -> str`：输入为签名中的参数；输出为 `str`。用途：计算实现成本:数量 × 单价 × 品质加成。
#   - `_envelope(ok: bool, kind: str='', message: str='', data: str='') -> str`：输入为签名中的参数；输出为 `str`。用途：统一错误信封:失败也要变成模型可读的反馈。
#   - `dispatch(name: str, args: dict) -> str`：输入为签名中的参数；输出为 `str`。用途：执行工具并返回 JSON 信封:失败绝不抛出,都变成可读文本。
#   - `build_pouch() -> list[StructuredTool]`：输入为签名中的参数；输出为 `list[StructuredTool]`。用途：把注册表处理成 LangChain 工具,随 bind_tools 一起发给模型。
#   - `build_llm() -> ChatOpenAI`：输入为签名中的参数；输出为 `ChatOpenAI`。用途：装配 DeepSeek 客户端(OpenAI 兼容协议),配置全部来自环境变量。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `ChatMemory`：承载本节状态/数据；重点方法：context, add, compress。
#   - `AgentHarness`：承载本节状态/数据；重点方法：run。
#   - `DujieAgent`：承载本节状态/数据；重点方法：chat, action_report。
#   - `ScriptedLLM`：承载本节状态/数据；重点方法：invoke。
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
    print("[任务调度台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地离线演示可设 MOCK_LLM=1,用剧本模拟模型决策)")
    sys.exit(0)

SYSTEM_PROMPT = "你是任务调度台的助道者,回答学习、制作方案、工具开发问题要简洁、准确、有项目侠味。"

# ---- 工具层:s1 注册表 + 分发器,原样沿用 ----
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
    """把注册表处理成 LangChain 工具,随 bind_tools 一起发给模型。"""
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
        """协作者发问:记轮次、走 Harness,返回终答。"""
        # TODO: 补全发问逻辑
        # 提示: turn_count 自增;打印 f"\n—— 第 {self.turn_count} 轮: {user_text}";return self.harness.run(user_text)
        raise NotImplementedError("t72-agent-layer-s6 尚未实现:请按 TODO 提示补全发问逻辑")

    def action_report(self) -> str:
        """输出本次运行的可观测性汇总:轮次、工具调用、记忆规模。"""
        # TODO: 补全行动报告
        # 提示: 用 "\n".join 拼四行:标题 / 对话轮数 / 工具调用次数 / 记忆规模(最近消息条数 + 摘要字数)
        raise NotImplementedError("t72-agent-layer-s6 尚未实现:请按 TODO 提示补全行动报告")


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
    {"content": "", "tool_calls": [{"name": "search_knowledge", "args": {"query": "基础阶段丹"}, "id": "call_1"}]},
    {"content": "基础阶段丹以九转灵草为引,文火炼足四十九日,配方详见资料。"},
    # 第二问:成本计算工具,同样 2 次迭代
    {"content": "", "tool_calls": [{"name": "calc_forge_cost", "args": {"item_name": "展示素材", "quantity": 3, "unit_cost": 120, "rarity": "精品"}, "id": "call_2"}]},
    {"content": "三件精品展示素材共需 540 预算点,已在账房记下。"},
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
    print("—— 任务调度台开张 ——")
    print("学习者: 活动方案怎么制作?")
    print("任务调度台:", agent.chat("活动方案怎么制作?"))
    print("学习者: 三件精品展示素材多少钱?")
    print("任务调度台:", agent.chat("三件精品展示素材多少钱?"))
    print("学习者: 好,我们继续。")
    print("任务调度台:", agent.chat("好,我们继续。"))
    print()
    print(agent.action_report())
    print("\n[检查] 剧本全部消耗:", not script)
    print("[检查] 摘要已生成:", bool(agent.memory.summary))
    print("[检查] 摘要内容:", agent.memory.summary)
    print("[检查] 窗口剩余:", len(agent.memory.messages))
    assert not script
    assert bool(agent.memory.summary)
    assert "活动方案怎么制作?" in agent.memory.summary
    assert len(agent.memory.messages) == 4  # max_turns=2 → 预算 4 条


if __name__ == "__main__":
    main()
