"""社团工具箱 v0.3 —— 新增文本工具:统计与大小写转换。"""
# ????????? Agent ????????????count_text ? convert_case????????????????????????????Python ??????????????t30-s2???????????????????????
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


_SAFE_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
             ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
             ast.USub: operator.neg}  # 运算符白名单(同 s2)


def _eval_node(node):
    """递归求值 AST 节点;白名单外的语法一律 raise,绝不动用 eval。"""
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("表达式含有不允许的语法")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式,支持 + - * / ** % 与括号,如「3 * (4 + 5)」。用户要求算账、算数时使用。"""
    try:
        result = _eval_node(ast.parse(expression, mode="eval"))
        return str(round(result, 6)) if isinstance(result, float) else str(result)
    except (ValueError, SyntaxError, ZeroDivisionError):
        return f"错误:无法计算表达式 {expression!r}"


@tool
def count_text(text: str) -> str:
    """统计文本的字符数、单词数和行数。用户问一段文字有多长、多少字时使用。"""
    # TODO: 统计文本的字符数、单词数与行数,拼成描述字符串返回
    # 提示:字符数 len(text);单词数 len(text.split());行数 text.count("\n") + 1
    raise NotImplementedError("s3-count-text 尚未实现:请按 TODO 提示完成文本统计")


@tool
def convert_case(text: str, mode: str = "upper") -> str:
    """转换英文大小写,mode 可选 upper(全大写)/ lower(全小写)/ title(首字母大写)。"""
    # TODO: 按 mode 转换大小写,非法 mode 返回「错误:」开头的提示
    # 提示:用 dict 分发替代 if-elif,例如 {upper: str.upper, lower: str.lower, title: str.title}
    raise NotImplementedError("s3-convert-case 尚未实现:请按 TODO 提示完成大小写转换")


def main() -> None:
    poem = "床前明月光\n疑是地上霜\n举头望明月\n低头思故乡"
    print("文本统计:", count_text(poem))
    # 三种合法模式各试一次,再加一个非法模式验证错误提示
    print("转大写:", convert_case("hello agent", "upper"))
    print("转小写:", convert_case("HELLO AGENT", "lower"))
    print("转标题:", convert_case("hello agent", "title"))
    print("非法模式:", convert_case("hello agent", "shout"))


if __name__ == "__main__":
    main()
