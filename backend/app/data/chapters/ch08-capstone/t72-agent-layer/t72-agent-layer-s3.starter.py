"""终期交付 · s3:记忆层,滑动窗口与摘要压缩

LLM 天生无状态:每一轮对话都要把历史重新喂回去。ChatMemory 用
「滑动窗口 + 摘要压缩」兜住 token 成本——最近 max_turns 轮完整保留,
更早的对话只留 user 提问,压成摘要继续参与上下文。
"""


# === 学习契约（面向学生）===
# 本节目标：记忆层:滑动窗口与摘要压缩。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `search_knowledge(query: str) -> str`：输入为签名中的参数；输出为 `str`。用途：检索构建资料:整句子串匹配,取第一条命中(模拟 RAG 检索)。
#   - `calc_forge_cost(item_name: str, quantity: int, unit_cost: float, rarity: str='凡品') -> str`：输入为签名中的参数；输出为 `str`。用途：计算实现成本:数量 × 单价 × 品质加成。
#   - `_envelope(ok: bool, kind: str='', message: str='', data: str='') -> str`：输入为签名中的参数；输出为 `str`。用途：统一错误信封:失败也要变成模型可读的反馈。
#   - `dispatch(name: str, args: dict) -> str`：输入为签名中的参数；输出为 `str`。用途：执行工具并返回 JSON 信封:失败绝不抛出,都变成可读文本。
#   - `build_pouch() -> list[StructuredTool]`：输入为签名中的参数；输出为 `list[StructuredTool]`。用途：把注册表处理成 LangChain 工具,随 bind_tools 一起发给模型。
#   - `build_llm() -> ChatOpenAI`：输入为签名中的参数；输出为 `ChatOpenAI`。用途：装配 DeepSeek 客户端(OpenAI 兼容协议),配置全部来自环境变量。
#   - `run_turn(user_text: str) -> None`：输入为签名中的参数；输出为 `None`。用途：一个带记忆的回合:入记忆 → 模型决策 → 执行工具 → 答复入记忆 → 压缩。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `ChatMemory`：承载本节状态/数据；重点方法：context, add, compress。
#   - `ScriptedLLM`：承载本节状态/数据；重点方法：invoke。
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import json
import os
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
    """短期记忆:最近窗口完整保留,超预算部分压缩成摘要。"""

    def __init__(self, max_turns: int = 3):
        self.max_turns = max_turns
        self.messages: list = []   # 窗口内的原始消息
        self.summary = ""          # 已压缩的早期对话摘要

    def context(self) -> list:
        """记忆的对外窗口:system + 摘要 + 窗口内消息。"""
        ctx = [{"role": "system", "content": SYSTEM_PROMPT}]
        if self.summary:
            ctx.append({"role": "system", "content": self.summary})
        ctx += self.messages
        return ctx

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.compress()

    def compress(self) -> None:
        """超预算时:最旧的 user 提问压进摘要,窗口裁剪到最近 budget 条。"""
        # TODO: 补全滑动窗口 + 摘要压缩
        # 提示: budget = self.max_turns * 2,超过预算才压缩;最旧的 user 提问用 "; ".join 拼成 chunk;chunk 非空时挂到 self.summary(前缀「已压缩对话:」);窗口只留最近 budget 条
        raise NotImplementedError("t72-agent-layer-s3 尚未实现:请按 TODO 提示补全记忆压缩")


class ScriptedLLM:
    """离线剧本模型:invoke 时按顺序吐出剧本里的回复,无 Key 演示与测试用。"""

    def __init__(self, script: list):
        self.script = script  # 引用共享:invoke 的 pop 直接消费调用方剧本

    def invoke(self, messages: list):
        if not self.script:
            raise RuntimeError("剧本已耗尽:调用次数与剧本对不上")
        return AIMessage(**self.script.pop(0))


script = [
    {"content": "", "tool_calls": [{"name": "search_knowledge", "args": {"query": "基础阶段丹"}, "id": "call_1"}]},
    {"content": "基础阶段丹要以九转灵草为引,文火炼足四十九日;配方详见资料。"},
    {"content": "", "tool_calls": [{"name": "search_knowledge", "args": {"query": "故障活动方案"}, "id": "call_2"}]},
    {"content": "上线验收活动方案在丹房二层,需避雷木作辅料,详情可查资料。"},
    {"content": "窗口里还剩最近 6 条消息,更早的已经压进摘要了。"},
    {"content": "最早那句「活动方案怎么制作?」已被压缩进摘要,我依然记得。"},
]

if MOCK:
    llm = ScriptedLLM(script)
else:
    llm = build_llm().bind_tools(build_pouch())

memory = ChatMemory(max_turns=3)


def run_turn(user_text: str) -> None:
    """一个带记忆的回合:入记忆 → 模型决策 → 执行工具 → 答复入记忆 → 压缩。"""
    memory.add("user", user_text)
    messages = list(memory.context())
    reply = llm.invoke(messages)
    if reply.tool_calls:
        # TODO: 补全工具执行半回合:决策入上下文 → 逐个执行 → 结果回传 → 再 invoke 拿最终答复
        # 提示: messages.append(reply);对每个 call 调 dispatch 并打印 f"  ◆ {call['name']} -> {text}";再 messages.append(ToolMessage(content=text, tool_call_id=call["id"]));最后 reply = llm.invoke(messages)
        raise NotImplementedError("t72-agent-layer-s3 尚未实现:请按 TODO 提示补全工具执行半回合")
    print("任务调度台:", reply.content)
    memory.add("assistant", reply.content)


def main() -> None:
    for q in ["活动方案怎么制作?", "那故障活动方案在哪炼?", "现在窗口还剩几条?", "最早问的那句还记得吗?"]:
        print(f"\n—— 学习者问: {q}")
        run_turn(q)
    print("\n[检查] 剧本全部消耗:", not script)
    print("[检查] 摘要内容:", memory.summary)
    print("[检查] 摘要含最早提问:", "活动方案怎么制作?" in memory.summary)
    print("[检查] 窗口剩余:", len(memory.messages))
    assert not script and "活动方案怎么制作?" in memory.summary


if __name__ == "__main__":
    main()
