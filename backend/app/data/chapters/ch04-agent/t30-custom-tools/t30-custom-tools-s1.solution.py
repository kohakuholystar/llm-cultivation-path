"""百宝囊 v0.1 —— 手写 @tool 装饰器,打下工具型 Agent 的地基。"""
import random
from datetime import datetime

TOOLBOX = {}  # 工具注册表:工具名 -> 函数,Agent 靠它发现法宝


def tool(func):
    """工具装饰器:贴元数据并登记(函数的 docstring 就是工具描述)。"""
    func.tool_name = func.__name__                       # 给函数对象贴上工具名标签
    func.tool_description = (func.__doc__ or "暂无描述").strip()  # docstring 即说明书
    TOOLBOX[func.__name__] = func                        # 登记进注册表
    return func                                          # 原样返回,函数功能不变


@tool
def system_time() -> str:
    """获取当前时间,格式 YYYY-MM-DD HH:MM:SS。用户问「现在几点/今天几号」时使用。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def roll_dice(sides: int = 6) -> str:
    """掷骰子并返回点数,sides 为面数(默认 6)。用户想随机做决定时使用。"""
    return f"掷出了 {random.randint(1, sides)} 点" if sides >= 2 else "错误:骰子至少要有 2 个面"


def _secret_sauce() -> str:
    """内部函数:没贴 @tool,不会被登记进百宝囊。"""
    return "我是内部实现细节,不对外开放"


def make_tool_by_hand():
    """对照实验:手动做一遍装饰器做的事,理解 @tool 只是语法糖。"""
    def hello() -> str:
        """打个招呼。用户想测试百宝囊是否工作时使用。"""
        return "你好,我是手动登记的法宝"
    return tool(hello)  # 等价于在 hello 定义上方写 @tool


def show_toolbox() -> None:
    """打印百宝囊清单:名称 + 描述,检查装饰器登记了哪些法宝。"""
    print(f"百宝囊中共有 {len(TOOLBOX)} 件法宝:")
    for name, func in TOOLBOX.items():
        print(f"  - {name}: {func.tool_description}")


def find_tool(name: str):
    """按名字从百宝囊取工具;找不到时打印提示并返回 None。"""
    if name not in TOOLBOX:
        print(f"未找到工具: {name}")
        return None
    return TOOLBOX[name]


def main() -> None:
    make_tool_by_hand()  # 手动登记第三件法宝,验证 @tool 就是语法糖
    show_toolbox()
    # 装饰器不改变函数本身,仍可照常直接调用
    print("直接调用:", system_time())
    print("直接调用:", roll_dice(6))
    # 也可以按名字从注册表取出再调用——这正是 Agent 使用工具的方式
    dice = find_tool("roll_dice")
    if dice is not None:
        print("按名调用:", dice(20))
    print("内部函数已登记:", "_secret_sauce" in TOOLBOX)  # False:没贴 @tool 不进表
    find_tool("fly_to_moon")  # 故意找个不存在的工具,看看兜底行为


if __name__ == "__main__":
    main()
