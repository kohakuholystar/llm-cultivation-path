"""社团工具箱 · t31-s2:动作解析器 —— 用正则把模型输出解析成结构化意图。"""

# ?????????????????????????parse_llm_output?????????????????? ParseError ???????re???????t31-s1??????????????????????????
import ast, collections, operator, os, re, sys

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
# TODO: 定义 ACTION_RE:匹配 "Thought: ... / Action: ... / Action Input: ..." 三段
# 提示:re.compile(r"Thought:\s*(.*?)\s*\nAction:\s*(.*?)\s*\nAction Input:\s*(.*)", re.S)


class ParseError(ValueError): """模型输出不遵守格式契约时抛出。"""


AgentAction = collections.namedtuple("AgentAction", ["thought", "tool", "tool_input"])  # 要调工具
AgentFinish = collections.namedtuple("AgentFinish", ["thought", "answer"])  # 宣布收尾


def parse_llm_output(text: str):
    """解析为 AgentFinish 或 AgentAction;都不匹配则抛 ParseError。"""
    # TODO: 先判收尾再判行动;都不命中则 raise ParseError;分组值记得 .strip()
    # 提示:FINAL_RE.search(text) 命中返回 AgentFinish(m.group(1).strip(), m.group(2).strip());
    #       ACTION_RE.search(text) 命中返回 AgentAction(m.group(1).strip(), m.group(2).strip(), m.group(3).strip());
    #       都不命中 raise ParseError(f"输出不符合契约: {text[:80]}...")
    raise NotImplementedError("t31-s2-parse-output 尚未实现:请按 TODO 提示完成解析")

def run_parser_tests() -> None:
    """离线自检:行动、收尾、坏样本三类输出都必须被正确处理。"""
    samples = ['Thought: 先算 (3 + 4) * 5\nAction: calculate\nAction Input: {"expression": "(3 + 4) * 5"}',
               "Thought: 信息足够了\nFinal Answer: 结果是 35。",
               "我直接告诉你答案吧"]  # 坏样本:必须抛 ParseError
    for text in samples:
        try: print("解析结果:", parse_llm_output(text))
        except ParseError as exc: print("按预期捕获 ParseError:", exc)

def main() -> None:
    run_parser_tests()
    if not os.environ.get("MOCK_LLM") and not os.environ.get("OPENAI_API_KEY"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)
    output = call_llm(build_prompt("帮我算 (3 + 4) * 5"))
    print("\n===== 模型输出的解析结果 =====")
    print(parse_llm_output(output))


if __name__ == "__main__":
    main()
