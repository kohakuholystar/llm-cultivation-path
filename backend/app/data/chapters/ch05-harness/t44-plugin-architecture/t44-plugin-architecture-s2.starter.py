"""乾坤圈 · s2:生命周期状态机

插件的一生要按规矩走:installed -> active -> inactive -> uninstalled。
本步用显式状态机管理迁移,非法迁移直接 raise,白名单 + 模板方法,
把「纪律」写进代码。
"""
from abc import ABC, abstractmethod


ST_INSTALLED = "installed"
ST_ACTIVE = "active"
ST_INACTIVE = "inactive"
ST_UNINSTALLED = "uninstalled"


class PluginStateError(Exception):
    """非法状态迁移时抛出。"""


class Plugin(ABC):
    def __init__(self, name, version, description):
        self.name = name
        self.version = version
        self.description = description

    @abstractmethod
    def run(self, text):
        """处理一条输入。"""

    def on_install(self):
        """安装:分配资源。"""

    def on_activate(self):
        """激活:开始对外服务。"""

    def on_deactivate(self):
        """停用:停止对外服务。"""

    def on_uninstall(self):
        """卸载:释放资源。"""


class EchoPlugin(Plugin):
    def run(self, text):
        return f"[echo] {text}"

    def on_install(self):
        print("  [echo] 安装:分配资源")

    def on_activate(self):
        print("  [echo] 激活:开始监听请求")

    def on_deactivate(self):
        print("  [echo] 停用:停止监听")

    def on_uninstall(self):
        print("  [echo] 卸载:释放资源")


class UpperPlugin(Plugin):
    def run(self, text):
        return f"[upper] {text.upper()}"


class PluginManager:
    VALID_ACTIVATE = {ST_INSTALLED: ST_ACTIVE}
    VALID_DEACTIVATE = {ST_ACTIVE: ST_INACTIVE}
    VALID_UNINSTALL = {ST_INSTALLED: ST_UNINSTALLED, ST_INACTIVE: ST_UNINSTALLED}

    def __init__(self):
        self._plugins = {}
        self._states = {}

    def install(self, plugin):
        if plugin.name in self._plugins:
            raise PluginStateError(f"插件 {plugin.name} 已存在,请先卸载")
        self._plugins[plugin.name] = plugin
        self._states[plugin.name] = ST_INSTALLED
        plugin.on_install()
        print(f"  [manager] {plugin.name} -> installed")

    def activate(self, name):
        # TODO: 校验迁移,置为 active 并触发 on_activate
        # 提示: 状态不在 self.VALID_ACTIVATE 就 raise PluginStateError(f"插件 {name} 当前状态 {self._states.get(name)},不能激活");
        #       否则 self._states[name] = ST_ACTIVE;self._plugins[name].on_activate();print(f"  [manager] {name} -> active")
        raise NotImplementedError("t44-plugin-architecture-s2 尚未实现:请按 TODO 提示实现 activate")

    def deactivate(self, name):
        # TODO: 校验迁移,置为 inactive 并触发 on_deactivate
        # 提示: 状态不在 self.VALID_DEACTIVATE 就 raise PluginStateError(f"插件 {name} 当前状态 {self._states.get(name)},不能停用");
        #       否则 self._states[name] = ST_INACTIVE;self._plugins[name].on_deactivate();print(f"  [manager] {name} -> inactive")
        raise NotImplementedError("t44-plugin-architecture-s2 尚未实现:请按 TODO 提示实现 deactivate")

    def uninstall(self, name):
        # TODO: 先拦截运行中的 active 状态,再校验迁移,通过后卸载并清理登记
        # 提示: state == ST_ACTIVE 先 raise PluginStateError(f"插件 {name} 还在运行,请先停用再卸载");
        #       再查 VALID_UNINSTALL;通过则 on_uninstall()、del 两个字典、print(f"  [manager] {name} -> uninstalled")
        raise NotImplementedError("t44-plugin-architecture-s2 尚未实现:请按 TODO 提示实现 uninstall")

    def active_plugins(self):
        return [n for n, s in self._states.items() if s == ST_ACTIVE]

    def summary(self):
        return " ".join(f"{n}={s}" for n, s in self._states.items())


def main():
    mgr = PluginManager()
    mgr.install(EchoPlugin("echo", "1.0.0", "回声通道"))
    mgr.install(UpperPlugin("upper", "1.0.0", "大写通道"))
    mgr.activate("echo")
    mgr.activate("upper")
    print(f"当前状态: {mgr.summary()}")
    print(f"活跃插件 {len(mgr.active_plugins())} 个")
    try:
        mgr.activate("upper")
    except PluginStateError as exc:
        print(f"拦截成功! {exc}")
    mgr.deactivate("upper")
    mgr.uninstall("upper")
    print(f"当前状态: {mgr.summary()}")


if __name__ == "__main__":
    main()
