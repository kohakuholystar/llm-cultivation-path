"""百宝囊 · t31-s6:上限保护与健壮性 —— 把玩具循环打磨成生产级 Agent。"""

import ast, collections, json, operator, os, re, sys

BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
REACT_INSTRUCTION = """你是「百宝囊」Agent,借助工具完成任务。每轮严格按格式输出,不要输出其他内容:
Thought: 思考 / Action: 工具名 / Action Input: JSON 参数(无参数写 {})
掌握足够信息后改输出: Thought: 总结 + Final Answer: 最终答案"""

TOOLBOX = {}  # 工具注册表(沿用 t30):工具名 -> 函数


def tool(func):  # 工具装饰器(沿用 t30):docstring 即说明书,登记进 TOOLBOX
    func.tool_description = (func.__doc__ or "暂无描述").strip()
    TOOLBOX[func.__name__] = func
    return func


_SAFE_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}  # 运算符白名单(沿用 t30)


def _eval_node(node):  # AST 白名单递归求值,绝不用 eval(沿用 t30)
    if isinstance(node, ast.Expression): return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)): return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS: return _SAFE_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    raise ValueError("表达式含有不允许的语法")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式,支持 + - * / ** 与括号,如「(3 + 4) * 5」。算不了时返回「错误:」开头的说明。"""
    try: return str(round(_eval_node(ast.parse(expression, mode="eval")), 6))
    except (ValueError, SyntaxError, ZeroDivisionError): return f"错误:无法计算表达式 {expression!r}"


TOOL_MANUAL = "法宝图鉴:\n" + "\n".join(f"- {n}: {f.tool_description}" for n, f in TOOLBOX.items())  # 注册表自动生成说明书

def build_prompt(question: str, scratchpad: str = "") -> str:  # 法宝图鉴 + 问题 + 历史轨迹(scratchpad)
    return f"{TOOL_MANUAL}\n\n问题: {question}\n\n已完成的步骤:\n{scratchpad}\n请输出下一轮(以 Thought 开头):"

MOCK_SCRIPT = ['Thought: 先算 (3 + 4) * 5。\nAction: calculate\nAction Input: {"expression": "(3 + 4) * 5"}', 'Thought: 得到 35,接下来乘以 2。\nAction: calculate\nAction Input: {"expression": "35 * 2"}', "Thought: 算出 70,可以收尾。\nFinal Answer: (3 + 4) * 5 = 35,35 × 2 = 70,最终答案是 70。"]


def mock_llm(prompt: str) -> str:  # MOCK_LLM=stuck 时模拟死循环,验证保护机制
    if os.environ.get("MOCK_LLM") == "stuck": return 'Thought: 我再算一次。\nAction: calculate\nAction Input: {"expression": "(3 + 4) * 5"}'
    return MOCK_SCRIPT.pop(0) if len(MOCK_SCRIPT) > 1 else MOCK_SCRIPT[0]

def call_llm(prompt: str) -> str:  # 调一次 DeepSeek 并返回文本;MOCK_LLM=1 时走假模型
    if os.environ.get("MOCK_LLM"): return mock_llm(prompt)
    from openai import OpenAI
    resp = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=BASE_URL).chat.completions.create(
        model=MODEL_NAME, temperature=0,  # Agent 场景要确定性
        messages=[{"role": "system", "content": REACT_INSTRUCTION}, {"role": "user", "content": prompt}])
    return resp.choices[0].message.content or ""

FINAL_RE = re.compile(r"Thought:\s*(.*?)\s*\nFinal Answer:\s*(.*)", re.S)
ACTION_RE = re.compile(r"Thought:\s*(.*?)\s*\nAction:\s*(.*?)\s*\nAction Input:\s*(.*)", re.S)


class ParseError(ValueError): """模型输出不遵守格式契约时抛出。"""


AgentAction = collections.namedtuple("AgentAction", ["thought", "tool", "tool_input"])  # 要调工具
AgentFinish = collections.namedtuple("AgentFinish", ["thought", "answer"])  # 宣布收尾


def parse_llm_output(text: str):
    """解析为 AgentFinish 或 AgentAction;都不匹配则抛 ParseError。"""
    m = FINAL_RE.search(text)  # 先判收尾,否则 Final Answer 正文里的 Action 字样会误判
    if m: return AgentFinish(m.group(1).strip(), m.group(2).strip())
    m = ACTION_RE.search(text)
    if m: return AgentAction(m.group(1).strip(), m.group(2).strip(), m.group(3).strip())
    raise ParseError(f"输出不符合契约: {text[:80]}...")

def run_action(name: str, raw_input: str) -> str:  # Action → 真实调用 → Observation;错误一律变文本(沿用 t30 dispatch 思想)
    func = TOOLBOX.get(name)
    if func is None: return f"错误:没有工具 {name!r},可用: {'、'.join(TOOLBOX)}"
    try:
        kwargs = json.loads(raw_input or "{}")
        if not isinstance(kwargs, dict): raise ValueError("必须是 JSON 对象")
        return str(func(**kwargs))
    except Exception as exc: return f"错误:执行失败({type(exc).__name__}: {exc})"

class Trajectory:
    """执行轨迹:Agent 的"飞行记录仪",可存盘、可回放、可做评测数据。"""

    def __init__(self, question: str):
        self.question, self.records, self.final_answer = question, [], ""

    def add(self, thought: str, action: str, action_input: str, observation: str) -> None:
        self.records.append({"thought": thought, "action": action, "action_input": action_input, "observation": observation})

    def as_scratchpad(self) -> str:  # 把轨迹拼回提示词,充当短期记忆
        return "\n".join(f"Thought: {r['thought']}\nAction: {r['action']}\nAction Input: {r['action_input']}\nObservation: {r['observation']}" for r in self.records)

    def save(self, path: str) -> str:  # 存盘为 JSON:问题 + 每轮记录 + 最终答案;返回路径方便链式调用
        json.dump({"question": self.question, "answer": self.final_answer, "records": self.records}, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return path


def replay(path: str) -> None:  # 从 JSON 加载轨迹并原样回放(只读记录,不重新调模型)
    data = json.load(open(path, encoding="utf-8"))
    print(f"===== 轨迹回放: {data['question']} =====")
    for i, r in enumerate(data["records"], 1): print(f"[第 {i} 轮] {r['thought']}\n  Action: {r['action']}  Input: {r['action_input']}\n  Observation: {r['observation']}")
    print("最终答案:", data["answer"])

def run_react(question: str, max_steps: int = 6) -> Trajectory:
    """主循环(生产版):上限保护 + 重复动作检测 + 解析失败自我纠错 + 异常兜底。"""
    traj, last_signature = Trajectory(question), ""
    for _ in range(max_steps):
        try: parsed = parse_llm_output(call_llm(build_prompt(question, traj.as_scratchpad())))
        except ParseError as exc:  # 解析失败:喂回纠错提示,给模型一次自我纠正的机会
            traj.add("", "<格式错误>", "", f"输出不符合契约({exc}),请重新输出"); continue
        except Exception as exc:  # 网络抖动、限流等:体面收尾,不抛 traceback
            traj.final_answer = f"调用模型失败({type(exc).__name__}),请稍后重试。"; return traj
        if isinstance(parsed, AgentFinish):
            traj.final_answer = parsed.answer
            return traj
        signature = f"{parsed.tool}|{parsed.tool_input}"
        if signature == last_signature:  # 重复动作:模型卡死,强制收尾
            traj.final_answer = "模型在重复同一个动作,判定陷入死循环,强制收尾。"; return traj
        last_signature = signature
        traj.add(parsed.thought, parsed.tool, parsed.tool_input, run_action(parsed.tool, parsed.tool_input))
    traj.final_answer = f"达到循环上限 {max_steps} 轮,强制收尾。"
    return traj

def main() -> None:
    if not os.environ.get("MOCK_LLM") and not os.environ.get("OPENAI_API_KEY"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)
    traj = run_react("帮我算 (3 + 4) * 5,再把结果乘以 2。")
    replay(traj.save("baibaonang_trajectory.json"))


if __name__ == "__main__":
    main()
