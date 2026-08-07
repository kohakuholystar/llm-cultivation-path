"""百宝囊 v1.0 —— 给法宝配质检线:单元测试 + 极简测试运行器。"""
import ast, inspect, json, operator, random
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
    """获取当前时间,格式 YYYY-MM-DD HH:MM:SS。仅当用户问「现在几点/今天几号」时使用,不要用来猜日期。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def roll_dice(sides: int = 6) -> str:
    """掷骰子并返回点数,sides 为面数(默认 6,必须 >= 2)。用户想随机做决定、玩桌游或抽签时使用。"""
    return f"掷出了 {random.randint(1, sides)} 点" if sides >= 2 else "错误:骰子至少要有 2 个面"


_SAFE_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
             ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod, ast.USub: operator.neg}  # 运算符白名单(同 s2)


def _eval_node(node):
    """递归求值 AST 节点;白名单外的语法一律 raise,绝不动用 eval。"""
    if isinstance(node, ast.Expression): return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)): return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("表达式含有不允许的语法")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式并返回结果字符串,支持 + - * / ** % 与括号,如「3 * (4 + 5)」。用户要求算账、算数、换算时使用;算不了时会返回「错误:」开头的说明。"""
    try:
        return str(round(_eval_node(ast.parse(expression, mode="eval")), 6))
    except (ValueError, SyntaxError, ZeroDivisionError):
        return f"错误:无法计算表达式 {expression!r}"


@tool
def count_text(text: str) -> str:
    """统计文本的字符数、单词数和行数。用户问一段文字有多长、多少字、多少行时使用。"""
    return f"字符数 {len(text)},单词数 {len(text.split())},行数 {text.count("\n") + 1}"


@tool
def convert_case(text: str, mode: str = "upper") -> str:
    """转换英文大小写,mode 必填三选一:upper(全大写)/ lower(全小写)/ title(首字母大写)。用户要求把英文变大写、变小写或标题化时使用。"""
    modes = {"upper": str.upper, "lower": str.lower, "title": str.title}
    return modes[mode](text) if mode in modes else f"错误:不支持 mode {mode!r},请从 upper / lower / title 中选择"


NOTES_DIR = Path("pouch_notes"); NOTES_DIR.mkdir(exist_ok=True)  # 笔记专用目录(同 s4)


def _safe_path(filename: str):
    """把文件名限制在 NOTES_DIR 内;试图 ../ 穿越时返回 None。"""
    path = (NOTES_DIR / filename).resolve()
    return path if path.parent == NOTES_DIR.resolve() else None


@tool
def write_note(filename: str, content: str) -> str:
    """把文字保存为 .txt 笔记,如 write_note("todo.txt", "买牛奶")。用户要求记录、保存、备忘某段内容时使用;已存在同名笔记会覆盖。"""
    path = _safe_path(filename) if filename.endswith(".txt") else None
    if path is None: return "错误:文件名非法,只支持百宝囊目录下的 .txt 文件"
    path.write_text(content, encoding="utf-8")
    return f"已保存 {filename}(共 {len(content)} 字符)"


@tool
def read_note(filename: str) -> str:
    """读取一篇 .txt 笔记的全文内容。用户要查看、引用之前保存的笔记时使用;笔记不存在会返回「错误:」开头的说明。"""
    path = _safe_path(filename)
    return path.read_text(encoding="utf-8") if path and path.exists() else f"错误:笔记 {filename} 不存在"


@tool
def list_notes() -> str:
    """列出百宝囊中所有 .txt 笔记的文件名。用户问「我保存了哪些笔记」时使用,返回顿号分隔的文件名列表。"""
    return "、".join(sorted(p.name for p in NOTES_DIR.glob("*.txt"))) or "还没有任何笔记"


def build_tool_manifest() -> str:
    """生成 JSON 法宝图鉴:名称 + 描述 + 参数名,即将来放进 system prompt 的工具清单。"""
    manifest = [{"name": n, "description": f.tool_description,
                 "parameters": list(inspect.signature(f).parameters)} for n, f in TOOLBOX.items()]
    return json.dumps(manifest, ensure_ascii=False, indent=2)


def dispatch(tool_name: str, **kwargs) -> str:
    """统一调用入口:按名字取工具并执行,Agent 主循环只跟它打交道。"""
    func = TOOLBOX.get(tool_name)
    if func is None: return f"错误:没有工具 {tool_name!r},请先查看法宝图鉴"
    try:
        return str(func(**kwargs))
    except TypeError as exc: return f"错误:参数不对——{exc}"


# TODO: 写 test_calculate():断言 calculate("1 + 2 * 3") == "7",
#   且 "错误" in calculate("1 / 0");再补一句危险表达式
#   "错误" in calculate("__import__('os')")
# 提示:calculate 的合法结果可直接用 == 比较;错误分支与注入攻击用 "错误" in 结果 判断
def test_calculate():  # 计算法宝用例:开心路径 + 除零 + 注入
    raise NotImplementedError("s6-test-calculate 尚未实现:请按 TODO 提示补全用例")


def test_text_tools():
    assert count_text("a b\nc") == "字符数 5,单词数 3,行数 2" and convert_case("abc", "upper") == "ABC" and "错误" in convert_case("abc", "shout")


def test_note_roundtrip():  # 写-读-列表闭环;独立文件名避免与演示文件互相污染
    assert write_note("unit.txt", "你好") == "已保存 unit.txt(共 2 字符)" and read_note("unit.txt") == "你好" and "unit.txt" in list_notes()


# TODO: 写 test_dispatch():断言 dispatch("calculate", expression="2 + 2") == "4",
#   且 "错误" in dispatch("fly_to_moon")
# 提示:dispatch 未知工具返回「错误:」开头;合法调用直接传关键字参数
def test_dispatch():  # dispatch 用例:调通 + 未知工具
    raise NotImplementedError("s6-test-dispatch 尚未实现:请按 TODO 提示补全用例")


def run_all_tests() -> bool:
    """极简测试运行器:收集所有 test_ 开头的函数,逐个执行并汇报。"""
    tests, passed = sorted((n, f) for n, f in globals().items() if n.startswith("test_")), 0
    for name, fn in tests:
        try:
            fn(); passed += 1; print(f"PASS {name}")
        except AssertionError as exc:  # 一个用例失败不应炸掉整场测试
            print(f"FAIL {name}: {exc}")
    print(f"测试结果: {passed}/{len(tests)} 通过")
    return passed == len(tests)


if __name__ == "__main__":
    print("全部测试通过,百宝囊质检合格!" if run_all_tests() else "存在失败用例,请修复")
