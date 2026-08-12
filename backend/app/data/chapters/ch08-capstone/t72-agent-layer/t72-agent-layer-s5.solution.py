"""终期交付 · s5:韧性设计,重试降级护体

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
        delay = self.base_delay
        for attempt in range(1, self.max_retries + 1):
            self.attempts += 1
            try:
                return self.llm.invoke(messages)
            except Exception as exc:  # noqa: BLE001
                if attempt == self.max_retries:
                    raise
                print(f"[重试] 第 {attempt} 次失败({exc}),{delay:.2f}s 后重试")
                time.sleep(delay)
                delay *= 2


class FlakyLLM:
    """抖动机模型:先按 fail_times 假装故障,再按剧本正常输出。"""

    def __init__(self, script: list, fail_times: int = 0):
        self.script = script  # 引用共享:invoke 的 pop 直接消费调用方剧本
        self.fail_times = fail_times

    def invoke(self, messages: list):
        if self.fail_times > 0:
            self.fail_times -= 1
            raise ConnectionError("网络抖动:网络暂时不稳定")
        if not self.script:
            raise RuntimeError("剧本已耗尽:调用次数与剧本对不上")
        return AIMessage(**self.script.pop(0))


class AgentHarness:
    """回合引擎(韧性版):决策走 _ask,重试耗尽就降级兜底。"""

    def __init__(self, llm, memory, max_steps: int = 5, fallback: str = "(兜底)任务调度台暂时失联,请稍后再试。"):
        self.llm = llm
        self.memory = memory
        self.max_steps = max_steps
        self.fallback = fallback
        self.trace: list = []      # 工具调用记录:(工具名, 参数)
        self.step_count = 0        # 本回合已执行的总步数

    def _ask(self, messages: list) -> AIMessage:
        """问一次模型:失败不抛出,降级成兜底文案。"""
        try:
            return self.llm.invoke(messages)
        except Exception as exc:  # noqa: BLE001
            print(f"[降级] 模型调用失败({exc}),启用兜底回复")
            return AIMessage(content=self.fallback)

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
    {"content": "", "tool_calls": [{"name": "search_knowledge", "args": {"query": "基础阶段丹"}, "id": "call_1"}]},
    {"content": "基础阶段丹以九转灵草为引,文火炼足四十九日,配方详见资料。"},
]

if MOCK:
    # 场景一:网络抖动 2 次后恢复 —— 重试护甲扛过 3 次失败并完成回合
    flaky1 = FlakyLLM(script1, fail_times=2)
    retry1 = WithRetry(flaky1)
    harness1 = AgentHarness(llm=retry1, memory=ChatMemory(max_turns=5))
    # 场景二:网络彻底断开 —— 3 次重试全败,_ask 降级兜底
    flaky2 = FlakyLLM([], fail_times=999)
    retry2 = WithRetry(flaky2)
    harness2 = AgentHarness(llm=retry2, memory=ChatMemory(max_turns=5))
else:
    llm = build_llm().bind_tools(build_pouch())
    harness1 = AgentHarness(llm=llm, memory=ChatMemory(max_turns=5))
    harness2 = None


def main() -> None:
    if MOCK:
        print("\n—— 学习者问: 活动方案怎么制作?(网络抖动 2 次,重试护甲扛过去)")
        reply1 = harness1.run("活动方案怎么制作?")
        print("任务调度台:", reply1)
        print("[检查] 场景一重试总尝试次数:", retry1.attempts)
        assert reply1 == "基础阶段丹以九转灵草为引,文火炼足四十九日,配方详见资料。"
        assert retry1.attempts == 4  # 3 次失败 + 1 次成功

        print("\n—— 学习者问: 网络彻底断了,三次重试后降级兜底")
        reply2 = harness2.run("当前服务状态如何?")
        print("任务调度台:", reply2)
        print("[检查] 场景二重试总尝试次数:", retry2.attempts)
        assert reply2 == harness2.fallback
        assert retry2.attempts == 3
        print("\n[检查] 重试与降级护甲全部生效。")
    else:
        for q in ["活动方案怎么制作?", "上线验收前要避开哪些故障难?"]:
            print(f"\n—— 学习者问: {q}")
            print("任务调度台:", harness1.run(q))
        print("\n[检查] 总步数:", harness1.step_count)


if __name__ == "__main__":
    main()
