"""Agent 运行时底座 · s1:插件协议与注册表

通用 Agent 运行时不该认识具体业务,只该认识「协议」。
本步定义插件协议 Plugin,再用注册表收纳、列清单、试运行、
注销——开闭原则的第一步:对扩展开放,对修改关闭。
"""


# === 学习契约（面向学生）===
# 本节目标：插件基座:Plugin 协议与注册表入圈。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `main() -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `Plugin`：承载本节状态/数据；重点方法：run, on_install。
#   - `EchoPlugin`：承载本节状态/数据；重点方法：run, on_install。
#   - `UpperPlugin`：承载本节状态/数据；重点方法：run。
#   - `PluginRegistry`：承载本节状态/数据；重点方法：register, unregister, get, names, count。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
from abc import ABC, abstractmethod


class Plugin(ABC):
    def __init__(self, name, version, description):
        self.name = name
        self.version = version
        self.description = description

    @abstractmethod
    def run(self, text):
        """处理一条输入,返回结果字符串。"""

    def on_install(self):
        """安装回调:给插件一个自我介绍的舞台。"""


class EchoPlugin(Plugin):
    def run(self, text):
        return f"[echo] {text}"

    def on_install(self):
        print("  [echo] 已安装:回声通道就绪")


class UpperPlugin(Plugin):
    def run(self, text):
        return f"[upper] {text.upper()}"


class PluginRegistry:
    def __init__(self):
        self._plugins = {}

    def register(self, plugin):
        # TODO: 按协议登记插件,并触发安装回调
        # 提示: self._plugins[plugin.name] = plugin;登记之后再调用 plugin.on_install()
        raise NotImplementedError("t44-plugin-architecture-s1 尚未实现:请按 TODO 提示实现 register")

    def unregister(self, name):
        # TODO: 注销插件:存在则删除并打印,不存在则打印提示
        # 提示: if name in self._plugins: del 后 print(f"  [{name}] 已注销");
        #       else: print(f"  [registry] 未找到插件 {name}")
        raise NotImplementedError("t44-plugin-architecture-s1 尚未实现:请按 TODO 提示实现 unregister")

    def get(self, name):
        return self._plugins.get(name)

    def names(self):
        return list(self._plugins)

    def count(self):
        return len(self._plugins)


def main():
    reg = PluginRegistry()
    reg.register(EchoPlugin("echo", "1.0.0", "回声通道"))
    reg.register(UpperPlugin("upper", "1.0.0", "大写通道"))
    print(f"当前注册 {reg.count()} 个插件: {reg.names()}")
    for name in reg.names():
        plugin = reg.get(name)
        print(f"  ◆ {name} v{plugin.version}: {plugin.description}")
    print("试运行:", reg.get("echo").run("你好,Agent 运行时底座"))
    print("试运行:", reg.get("upper").run("hello"))
    reg.unregister("echo")
    reg.unregister("ghost")
    print(f"剩 {reg.count()} 个插件: {reg.names()}")


if __name__ == "__main__":
    main()
