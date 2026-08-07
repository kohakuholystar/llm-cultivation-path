"""乾坤圈 · s1:插件协议与注册表

通用 Agent 运行时不该认识具体业务,只该认识「协议」。
本步定义插件协议 Plugin,再用注册表收纳、列清单、试运行、
注销——开闭原则的第一步:对扩展开放,对修改关闭。
"""
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
        self._plugins[plugin.name] = plugin
        plugin.on_install()

    def unregister(self, name):
        if name in self._plugins:
            del self._plugins[name]
            print(f"  [{name}] 已注销")
        else:
            print(f"  [registry] 未找到插件 {name}")

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
    print("试运行:", reg.get("echo").run("你好,乾坤圈"))
    print("试运行:", reg.get("upper").run("hello"))
    reg.unregister("echo")
    reg.unregister("ghost")
    print(f"剩 {reg.count()} 个插件: {reg.names()}")


if __name__ == "__main__":
    main()
