"""百宝囊 · t31-s1:格式契约 —— 约定 ReAct 输出格式,完成第一次 LLM 调用。"""

import ast, operator, os, sys

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

def build_prompt(question: str) -> str:  # 组装提示词:法宝图鉴 + 问题 + 开场引导
    # TODO: 返回提示词:法宝图鉴 + 问题 + 开场引导
    # 提示:f"{TOOL_MANUAL}\n\n问题: {question}\n\n请开始你的第一轮输出:"
    raise NotImplementedError("t31-s1-build-prompt 尚未实现:请按 TODO 提示拼接提示词")

def mock_llm(prompt: str) -> str:  # 离线假模型(设 MOCK_LLM=1 启用),返回一段符合契约的输出
    return 'Thought: 我先算 (3 + 4) * 5。\nAction: calculate\nAction Input: {"expression": "(3 + 4) * 5"}'

def call_llm(prompt: str) -> str:  # 调一次 DeepSeek 并返回文本;MOCK_LLM=1 时走假模型
    if os.environ.get("MOCK_LLM"): return mock_llm(prompt)
    from openai import OpenAI
    # TODO: 调 OpenAI SDK 发对话请求,返回回复文本
    # 提示:resp = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=BASE_URL).chat.completions.create(
    #       model=MODEL_NAME, temperature=0, messages=[system 契约, user 提示词])
    #       再返回 resp.choices[0].message.content or ""
    raise NotImplementedError("t31-s1-call-llm 尚未实现:请按 TODO 提示完成模型调用")

def main() -> None:
    # 联网前置检查:没配 Key 就引导退出,不让学习者看到 traceback
    if not os.environ.get("MOCK_LLM") and not os.environ.get("OPENAI_API_KEY"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)
    print(f"端点: {BASE_URL}  模型: {MODEL_NAME}")
    print(f"百宝囊已装填 {len(TOOLBOX)} 件法宝: {'、'.join(TOOLBOX)}")
    prompt = build_prompt("帮我算 (3 + 4) * 5")
    print("===== 发给模型的提示词 =====")
    print(prompt)
    print("\n===== 模型的原始输出 =====")
    print(call_llm(prompt))
    print("\n下一步:用正则把 Action 与 Action Input 从这段文本里解析出来。")


if __name__ == "__main__":
    main()
