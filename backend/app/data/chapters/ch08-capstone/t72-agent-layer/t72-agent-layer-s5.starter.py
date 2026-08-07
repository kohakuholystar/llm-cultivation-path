"""渡劫飞升 · s5:韧性设计,重试降级护体

真实世界里,模型 API 是脆弱的:网络抖动、限流、超时随时可能把一次
好好的工具调用变成事故。本步给 Harness 披上三层护甲——
1. WithRetry:失败自动重试,间隔指数退避,最多 max_retries 次;
2. FlakyLLM:按剧本「假装故障」的模型,专门用来本地演练故障场景;
3. AgentHarness._ask:重试全部失败后降级,用兜底文案体面收场。
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


class WithRetry:
    """重试护甲:invoke 失败自动重试,间隔指数退避,全败才抛出。"""

    def __init__(self, llm, max_retries: int = 3, base_delay: float = 0.05):
        self.llm = llm
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.attempts = 0  # 实际总尝试次数,供测试断言

    def invoke(self, messages: list):
        # TODO: 补全重试逻辑
        # 提示: delay 从 base_delay 起步,按 max_retries 循环;成功立即 return;失败未到上限则打印 [重试] 日志、time.sleep(delay) 后 delay *= 2;到上限原样 raise
        raise NotImplementedError("t72-agent-layer-s5 尚未实现:请按 TODO 提示补全重试逻辑")


class FlakyLLM:
    """抖动机模型:先按 fail_times 假装故障,再按剧本正常输出。"""

    def __init__(self, script: list, fail_times: int = 0):
        self.script = script  # 引用共享:invoke 的 pop 直接消费调用方剧本
        self.fail_times = fail_times

    def invoke(self, messages: list):
        # TODO: 补全抖动逻辑
        # 提示: fail_times 大于 0 时减一并抛 ConnectionError(灵脉抖动);剧本耗尽抛 RuntimeError;正常情况按剧本顺序返回 AIMessage
        raise NotImplementedError("t72-agent-layer-s5 尚未实现:请按 TODO 提示补全抖动逻辑")


class AgentHarness:
    """回合引擎(韧性版):决策走 _ask,重试耗尽就降级兜底。"""

    def __init__(self, llm, memory, max_steps: int = 5, fallback: str = "(兜底)渡劫台暂时失联,请稍后再试。"):
        self.llm = llm
        self.memory = memory
        self.max_steps = max_steps
        self.fallback = fallback
        self.trace: list = []      # 工具调用记录:(工具名, 参数)
        self.step_count = 0        # 本回合已执行的总步数

    def _ask(self, messages: list) -> AIMessage:
        """问一次模型:失败不抛出,降级成兜底文案。"""
        # TODO: 补全降级逻辑
        # 提示: try 里 return self.llm.invoke(messages);except 时打印 [降级] 日志,再 return AIMessage(content=self.fallback)
        raise NotImplementedError("t72-agent-layer-s5 尚未实现:请按 TODO 提示补全降级逻辑")

    def run(self, user_text: str) -> str:
        """执行一个完整回合:每一步要么是终答,要么是工具调用。"""
        self.memory.add("user", user_text)
        messages = list(self.memory.context())
        for _ in range(self.max_steps):
            self.step_count += 1
            decision = self._ask(messages)
            if not decision.tool_calls:
                self.memory.add("assistant", decision.content)
                return decision.content
            messages.append(decision)
            for call in decision.tool_calls:
                result = dispatch(call["name"], call["args"])
                self.trace.append((call["name"], call["args"]))
                print(f"  ◆ {call['name']} -> {result}")
                messages.append(ToolMessage(content=result, tool_call_id=call["id"]))
        self.memory.add("assistant", "已达最大步数,转人工接管。")
        return "已达最大步数,转人工接管。"


script1 = [
    # 一问一工具,2 次迭代出终答;前 2 次调用被 FlakyLLM 当成故障
    {"content": "", "tool_calls": [{"name": "search_knowledge", "args": {"query": "筑基丹"}, "id": "call_1"}]},
    {"content": "筑基丹以九转灵草为引,文火炼足四十九日,配方详见典籍。"},
]

if MOCK:
    # 场景一:灵脉抖动 2 次后恢复 —— 重试护甲扛过 3 次失败并完成回合
    flaky1 = FlakyLLM(script1, fail_times=2)
    retry1 = WithRetry(flaky1)
    harness1 = AgentHarness(llm=retry1, memory=ChatMemory(max_turns=5))
    # 场景二:灵脉彻底断开 —— 3 次重试全败,_ask 降级兜底
    flaky2 = FlakyLLM([], fail_times=999)
    retry2 = WithRetry(flaky2)
    harness2 = AgentHarness(llm=retry2, memory=ChatMemory(max_turns=5))
else:
    llm = build_llm().bind_tools(build_pouch())
    harness1 = AgentHarness(llm=llm, memory=ChatMemory(max_turns=5))
    harness2 = None


def main() -> None:
    if MOCK:
        print("\n—— 道友问: 筑基丹怎么炼?(灵脉抖动 2 次,重试护甲扛过去)")
        reply1 = harness1.run("筑基丹怎么炼?")
        print("渡劫台:", reply1)
        print("[检查] 场景一重试总尝试次数:", retry1.attempts)
        assert reply1 == "筑基丹以九转灵草为引,文火炼足四十九日,配方详见典籍。"
        assert retry1.attempts == 4  # 3 次失败 + 1 次成功

        print("\n—— 道友问: 灵脉彻底断了,三次重试后降级兜底")
        reply2 = harness2.run("今日运势如何?")
        print("渡劫台:", reply2)
        print("[检查] 场景二重试总尝试次数:", retry2.attempts)
        assert reply2 == harness2.fallback
        assert retry2.attempts == 3
        print("\n[检查] 重试与降级护甲全部生效。")
    else:
        for q in ["筑基丹怎么炼?", "渡劫前要避开哪些劫难?"]:
            print(f"\n—— 道友问: {q}")
            print("渡劫台:", harness1.run(q))
        print("\n[检查] 总步数:", harness1.step_count)


if __name__ == "__main__":
    main()
