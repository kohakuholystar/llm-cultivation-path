"""社团工具箱 v0.1 —— 手写 @tool 装饰器,打下工具型 Agent 的地基。"""
# 学习契约：目标：实现最小 @tool 注册机制，理解“函数元数据 + 注册表”的工具发现方式；补写：tool(func) 中的名称、说明提取与 TOOLBOX 登记。
# 关键接口：tool(func) 接收函数并返回同一函数，TOOLBOX 输出名称到可调用对象的映射。技术栈：Python 函数对象、装饰器、dict 注册表；前置：会定义函数与读取 __name__/__doc__；可观察结果：工具清单能列出并按名称找到已登记工具。
# 学习契约：目标：实现最小 @tool 注册机制，理解“函数元数据 + 注册表”的工具发现方式；补写：tool(func) 中的名称、说明提取与 TOOLBOX 登记。
# 关键接口：tool(func) 接收函数并返回同一函数，TOOLBOX 输出名称到可调用对象的映射。技术栈：Python 函数对象、装饰器、dict 注册表；前置：会定义函数与读取 __name__/__doc__；可观察结果：工具清单能列出并按名称找到已登记工具。
# 学习契约：目标是实现最小 @tool 注册机制，理解函数元数据与注册表如何让 Agent 发现工具。
# 补写 tool(func) 的名称/说明登记，以及 roll_dice；tool 输入函数并返回原函数，find_tool 输入名称并返回函数或 None。
# 技术栈：Python 装饰器、函数对象与 dict 注册表。前置：理解 __name__/__doc__；无需联网或 API Key。
# 完成后可观察到：工具清单列出已登记工具，且能按名称取回并调用。
import random
from datetime import datetime

TOOLBOX = {}  # 工具注册表:工具名 -> 函数,Agent 靠它发现工具


def tool(func):
    """工具装饰器:贴元数据并登记(函数的 docstring 就是工具描述)。"""
    # TODO: 给 func 贴 tool_name / tool_description 两个标签,登记进 TOOLBOX,最后原样返回
    # 提示: func.__name__ 取函数名;func.__doc__ 取 docstring(需 or "暂无描述" 兜底再 .strip());
    #       TOOLBOX[func.__name__] = func;最后 return func
    raise NotImplementedError("t30-custom-tools-s1 尚未实现:请按 TODO 提示补全 tool 装饰器")


@tool
def system_time() -> str:
    """获取当前时间,格式 YYYY-MM-DD HH:MM:SS。用户问「现在几点/今天几号」时使用。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# TODO: 用 @tool 装饰第二件工具 roll_dice(sides: int = 6) -> str
# 提示: docstring 写清「掷骰子返回点数,sides 为面数(默认 6),随机做决定时使用」;
#       函数体一行:sides >= 2 时返回 f"掷出了 {random.randint(1, sides)} 点",否则返回错误提示
raise NotImplementedError("t30-custom-tools-s1 尚未实现:请按 TODO 提示编写 roll_dice 工具")


def _secret_sauce() -> str:
    """内部函数:没贴 @tool,不会被登记进社团工具箱。"""
    return "我是内部实现细节,不对外开放"


def make_tool_by_hand():
    """对照实验:手动做一遍装饰器做的事,理解 @tool 只是语法糖。"""
    def hello() -> str:
        """打个招呼。用户想测试社团工具箱是否工作时使用。"""
        return "你好,我是手动登记的工具"
    return tool(hello)  # 等价于在 hello 定义上方写 @tool


def show_toolbox() -> None:
    """打印社团工具箱清单:名称 + 描述,检查装饰器登记了哪些工具。"""
    print(f"社团工具箱中共有 {len(TOOLBOX)} 件工具:")
    for name, func in TOOLBOX.items():
        print(f"  - {name}: {func.tool_description}")


def find_tool(name: str):
    """按名字从社团工具箱取工具;找不到时打印提示并返回 None。"""
    if name not in TOOLBOX:
        print(f"未找到工具: {name}")
        return None
    return TOOLBOX[name]


def main() -> None:
    make_tool_by_hand()  # 手动登记第三件工具,验证 @tool 就是语法糖
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
# 学习契约：目标：实现最小 @tool 注册机制，理解“函数元数据 + 注册表”的工具发现方式；补写：tool(func) 中的名称、说明提取与 TOOLBOX 登记。
# 关键接口：tool(func) 接收函数并返回同一函数，TOOLBOX 输出名称到可调用对象的映射。技术栈：Python 函数对象、装饰器、dict 注册表；前置：会定义函数与读取 __name__/__doc__；可观察结果：工具清单能列出并按名称找到已登记工具。
