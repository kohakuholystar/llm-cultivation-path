"""社团工具箱 · t31-s3:工具执行 —— 把解析出的 Action 变成 Observation。"""

# ??????????????????????run_action?????????????Observation ?????????????JSON????t31-s2???????????????????????
import ast, collections, json, operator, os, re, sys

BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
REACT_INSTRUCTION = """你是「社团工具箱」Agent,借助工具完成任务。每轮严格按格式输出,不要输出其他内容:
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


TOOL_MANUAL = "工具清单:\n" + "\n".join(f"- {n}: {f.tool_description}" for n, f in TOOLBOX.items())  # 注册表自动生成说明书

def build_prompt(question: str) -> str:  # 组装提示词:工具清单 + 问题 + 开场引导
    return f"{TOOL_MANUAL}\n\n问题: {question}\n\n请开始你的第一轮输出:"

def mock_llm(prompt: str) -> str:  # 离线假模型(设 MOCK_LLM=1 启用),返回一段符合契约的输出
    return 'Thought: 我先算 (3 + 4) * 5。\nAction: calculate\nAction Input: {"expression": "(3 + 4) * 5"}'

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
    # TODO: 解析 JSON 参数并执行工具;任何异常都翻译成「错误:」文本返回
    # 提示:json.loads(raw_input or "{}") 后需 isinstance 校验 dict;
    #       return str(func(**kwargs));except Exception as exc: return f"错误:执行失败({type(exc).__name__}: {exc})"
    raise NotImplementedError("t31-s3-run-action 尚未实现:请按 TODO 提示完成工具执行")

def main() -> None:
    # 联网前置检查(同前)
    if not os.environ.get("MOCK_LLM") and not os.environ.get("OPENAI_API_KEY"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)
    parsed = parse_llm_output(call_llm(build_prompt("帮我算 (3 + 4) * 5")))
    if isinstance(parsed, AgentAction):
        print(f"模型想调用 {parsed.tool},参数 {parsed.tool_input}")
        print("Observation:", run_action(parsed.tool, parsed.tool_input))
        print("\n下一步:把 Observation 拼回提示词,让模型带着结果继续下一轮。")
    else:
        print("模型直接给出答案:", parsed.answer)


if __name__ == "__main__":
    main()
