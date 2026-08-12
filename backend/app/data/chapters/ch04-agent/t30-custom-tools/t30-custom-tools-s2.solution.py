"""社团工具箱 v0.2 —— 新增计算器工具:用 AST 白名单安全求值,绝不用 eval。"""
import ast
import operator
import random
from datetime import datetime

TOOLBOX = {}  # 工具注册表:工具名 -> 函数


def tool(func):
    """工具装饰器:贴元数据并登记(函数的 docstring 就是工具描述)。"""
    func.tool_name = func.__name__
    func.tool_description = (func.__doc__ or "暂无描述").strip()
    TOOLBOX[func.__name__] = func
    return func


@tool
def system_time() -> str:
    """获取当前时间,格式 YYYY-MM-DD HH:MM:SS。用户问「现在几点/今天几号」时使用。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def roll_dice(sides: int = 6) -> str:
    """掷骰子并返回点数,sides 为面数(默认 6)。用户想随机做决定时使用。"""
    return f"掷出了 {random.randint(1, sides)} 点" if sides >= 2 else "错误:骰子至少要有 2 个面"


_SAFE_OPS = {  # 白名单:只放行这些运算符,函数调用/属性访问一律拒绝
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _eval_node(node):
    """递归求值 AST 节点;白名单外的语法一律 raise,绝不动用 eval。"""
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:  # 二元:+ - * / ** %
        return _SAFE_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:  # 一元:负号
        return _SAFE_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("表达式含有不允许的语法")  # 函数调用、变量名、属性访问都落到这


@tool
def calculate(expression: str) -> str:
    """计算数学表达式,支持 + - * / ** % 与括号,如「3 * (4 + 5)」。用户要求算账、算数时使用。"""
    try:
        result = _eval_node(ast.parse(expression, mode="eval"))  # 先解析成 AST 再白名单求值
        return str(round(result, 6)) if isinstance(result, float) else str(result)
    except (ValueError, SyntaxError, ZeroDivisionError):
        # 工具出错要返回可读字符串:LLM 读到后会自我纠正,traceback 只会打断主循环
        return f"错误:无法计算表达式 {expression!r}"


def main() -> None:
    # 正常计算:括号、乘方、取余都没问题
    print("计算 3 * (4 + 5) =", calculate("3 * (4 + 5)"))
    print("计算 2 ** 10 =", calculate("2 ** 10"))
    # 危险输入:__import__ 是函数调用节点,不在白名单,被安全拒绝
    print("攻击测试:", calculate("__import__('os').system('echo hacked')"))
    # 除零与语法错误:返回可读的错误字符串,而不是 traceback
    print("除零测试:", calculate("1 / 0"))
    print("语法错误:", calculate("1 +"))


if __name__ == "__main__":
    main()
