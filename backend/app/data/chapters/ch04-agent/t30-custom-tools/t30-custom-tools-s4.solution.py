"""社团工具箱 v0.4 —— 新增文件工具:只许在 pouch_notes/ 目录内活动的笔记读写。"""
import ast
import operator
import random
from datetime import datetime
from pathlib import Path

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
    return f"字符数 {len(text)},单词数 {len(text.split())},行数 {text.count("\n") + 1}"


@tool
def convert_case(text: str, mode: str = "upper") -> str:
    """转换英文大小写,mode 可选 upper(全大写)/ lower(全小写)/ title(首字母大写)。"""
    modes = {"upper": str.upper, "lower": str.lower, "title": str.title}
    return modes[mode](text) if mode in modes else f"错误:不支持 mode {mode!r}"


NOTES_DIR = Path("pouch_notes")  # 笔记专用目录:文件工具只许在这堵墙内活动
NOTES_DIR.mkdir(exist_ok=True)


def _safe_path(filename: str):
    """把文件名限制在 NOTES_DIR 内;试图 ../ 穿越时返回 None。"""
    path = (NOTES_DIR / filename).resolve()  # resolve 会把 ../ 归一化成真实绝对路径
    # 只有直接位于 NOTES_DIR 下的文件才放行,子目录与穿越一律拒绝
    return path if path.parent == NOTES_DIR.resolve() else None


@tool
def write_note(filename: str, content: str) -> str:
    """把文字保存为 .txt 笔记。用户要求记录、保存内容时使用,如 write_note("todo.txt", "买牛奶")。"""
    path = _safe_path(filename) if filename.endswith(".txt") else None  # 扩展名 + 路径双重把关
    if path is None:
        return "错误:文件名非法,只支持社团工具箱目录下的 .txt 文件"
    path.write_text(content, encoding="utf-8")  # 显式 UTF-8,避免平台默认编码坑
    return f"已保存 {filename}(共 {len(content)} 字符)"


@tool
def read_note(filename: str) -> str:
    """读取一篇 .txt 笔记的内容。用户要查看之前保存的笔记时使用。"""
    path = _safe_path(filename)
    return path.read_text(encoding="utf-8") if path and path.exists() else f"错误:笔记 {filename} 不存在"


@tool
def list_notes() -> str:
    """列出社团工具箱中所有 .txt 笔记的文件名。用户问保存了哪些笔记时使用。"""
    return "、".join(sorted(p.name for p in NOTES_DIR.glob("*.txt"))) or "还没有任何笔记"


def main() -> None:
    print(write_note("todo.txt", "1. 学完自定义工具\n2. 给工具写测试"))
    print("笔记列表:", list_notes())
    print("读取笔记:", read_note("todo.txt"))
    # 路径穿越攻击:试图写到社团工具箱目录之外,会被 _safe_path 拦截
    print("穿越攻击:", write_note("../evil.txt", "hack"))
    print("读取不存在的笔记:", read_note("ghost.txt"))


if __name__ == "__main__":
    main()
