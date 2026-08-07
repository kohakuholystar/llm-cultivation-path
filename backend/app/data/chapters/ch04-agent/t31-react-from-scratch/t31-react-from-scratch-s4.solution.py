"""百宝囊 · t31-s4:闭环 —— Thought-Action-Observation 主循环。"""

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

# 剧本假模型:按调用次序弹出回复,模拟一个会多步推理的模型(离线演示用)
MOCK_SCRIPT = ['Thought: 先算 (3 + 4) * 5。\nAction: calculate\nAction Input: {"expression": "(3 + 4) * 5"}', 'Thought: 得到 35,接下来乘以 2。\nAction: calculate\nAction Input: {"expression": "35 * 2"}', "Thought: 算出 70,可以收尾。\nFinal Answer: (3 + 4) * 5 = 35,35 × 2 = 70,最终答案是 70。"]


def mock_llm(prompt: str) -> str:  # MOCK_LLM=1 时替代真实模型
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

def format_scratchpad(trajectory: list) -> str:  # 把历史 T-A-O 拼回提示词——Agent 的"短期记忆"
    return "\n".join(f"Thought: {t}\nAction: {a}\nAction Input: {i}\nObservation: {o}" for t, a, i, o in trajectory)

def run_react(question: str, max_steps: int = 6) -> str:
    """ReAct 主循环:思考→行动→观察,直到 Final Answer 或触及循环上限。"""
    trajectory = []
    for step in range(1, max_steps + 1):
        parsed = parse_llm_output(call_llm(build_prompt(question, format_scratchpad(trajectory))))
        print(f"--- 第 {step} 轮 ---\nThought: {parsed.thought}")
        if isinstance(parsed, AgentFinish):
            print("Final Answer:", parsed.answer)
            return parsed.answer
        observation = run_action(parsed.tool, parsed.tool_input)
        print(f"Action: {parsed.tool}  Input: {parsed.tool_input}\nObservation: {observation}")
        trajectory.append((parsed.thought, parsed.tool, parsed.tool_input, observation))
    print(f"已到达循环上限 {max_steps},强制收尾。")
    return "抱歉,我在规定步数内没能得出结论。"

def main() -> None:
    # 联网前置检查(同前)
    if not os.environ.get("MOCK_LLM") and not os.environ.get("OPENAI_API_KEY"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)
    answer = run_react("帮我算 (3 + 4) * 5,再把结果乘以 2。")
    print("\n===== 最终答案 =====")
    print(answer)


if __name__ == "__main__":
    main()
