"""社团工具箱 v0.2 —— 新增计算器工具:用 AST 白名单安全求值,绝不用 eval。"""
# 学习契约：目标：实现 AST 白名单计算工具；补写：calculate 的安全求值逻辑。关键接口：calculate(expression: str) -> str；技术栈：ast、operator、装饰器注册表；前置：t30-s1；可观察结果：合法算式得到结果，危险节点被拒绝。
# ?????????? AST ???????????calculate ?????????????calculate(expression: str) -> str?????ast?operator???????????t30-s1????????????????????????
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
    # TODO: 处理二元运算 ast.BinOp 与一元运算 ast.UnaryOp,白名单外一律 raise ValueError
    # 提示: 先 isinstance 判断再查 type(node.op) in _SAFE_OPS;二元递归求值 node.left / node.right
    #       (一元是 node.operand);用 _SAFE_OPS[type(node.op)](...) 算出结果返回;
    #       所有分支都不匹配时 raise ValueError("表达式含有不允许的语法")
    raise NotImplementedError("t30-custom-tools-s2 尚未实现:请按 TODO 提示补全 BinOp/UnaryOp 分支与兜底")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式,支持 + - * / ** % 与括号,如「3 * (4 + 5)」。用户要求算账、算数时使用。"""
    # TODO: try 里用 _eval_node(ast.parse(expression, mode="eval")) 求值并转成字符串返回
    # 提示: 浮点结果先 round(结果, 6);except (ValueError, SyntaxError, ZeroDivisionError) 时
    #       返回 f"错误:无法计算表达式 {expression!r}"
    raise NotImplementedError("t30-custom-tools-s2 尚未实现:请按 TODO 提示实现 calculate 的 try/except 求值")


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
