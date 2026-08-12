"""Agent 运行时底座 · s5:总装成军

注册表、状态机、钩子、热加载四件套合体成 QiankunRuntime,
运行时不认识具体插件,新能力只是新注册一个插件。组合优于
继承,事件链串起整条请求流水线。
"""


# === 学习契约（面向学生）===
# 本节目标：总装成军:Agent 运行时底座插件化运行时。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `main() -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `Plugin`：承载本节状态/数据；重点方法：run, hooks, on_config_changed。
#   - `EchoPlugin`：承载本节状态/数据；重点方法：hooks, run, on_config_changed。
#   - `GuardPlugin`：承载本节状态/数据；重点方法：hooks, check。
#   - `HookBus`：承载本节状态/数据；重点方法：subscribe, publish。
#   - `QiankunRuntime`：承载本节状态/数据；重点方法：install, activate, active, load_config, hot_reload, handle。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import json
import os
import tempfile
from abc import ABC


class Plugin(ABC):
    def __init__(self, name, version, description):
        self.name = name
        self.version = version
        self.description = description

    def run(self, event, text):
        return "(无处理)"

    def hooks(self):
        return {}

    def on_config_changed(self, cfg):
        pass


class EchoPlugin(Plugin):
    def __init__(self):
        super().__init__("echo", "1.0.0", "回声通道")
        self.prefix = "raw"

    def hooks(self):
        return {"request_in": "run"}

    def run(self, event, text):
        print(f"  [echo/{self.prefix}] {text}")
        return f"[echo/{self.prefix}] {text}"

    def on_config_changed(self, cfg):
        self.prefix = cfg.get("prefix", "raw")
        print(f"  [echo] 前缀热更新为 {self.prefix}")


class GuardPlugin(Plugin):
    def __init__(self):
        super().__init__("guard", "1.0.0", "内容安检")

    def hooks(self):
        return {"request_in": "check"}

    def check(self, event, text):
        if "禁" in text:
            print("  [guard] 检测到违禁词,否决请求")
            return False
        return None


class HookBus:
    def __init__(self):
        self._subs = {}

    def subscribe(self, event, plugin):
        if event in plugin.hooks() and plugin not in self._subs.setdefault(event, []):
            self._subs[event].append(plugin)

    def publish(self, event, text):
        for plugin in self._subs.get(event, []):
            if getattr(plugin, plugin.hooks()[event])(event, text) is False:
                print(f"  [hook] {plugin.name} 否决事件 {event}")
                return False
        return True


class QiankunRuntime:
    def __init__(self, config_path):
        self.config_path = config_path
        self.bus = HookBus()
        self._plugins = {}
        self._states = {}
        self._fingerprint = ""

    def install(self, plugin):
        self._plugins[plugin.name] = plugin
        self._states[plugin.name] = "installed"
        print(f"  [manager] {plugin.name} installed")
        for event in ("request_in", "request_out"):
            self.bus.subscribe(event, plugin)

    def activate(self, name):
        # TODO: 校验状态后置为 active,非法迁移 raise ValueError
        # 提示: self._states.get(name) != "installed" 就 raise ValueError(f"插件 {name} 当前状态 {self._states.get(name)},不能激活");
        #       否则 self._states[name] = "active";print(f"  [manager] {name} active")
        raise NotImplementedError("t44-plugin-architecture-s5 尚未实现:请按 TODO 提示实现 activate")

    def active(self):
        return [n for n, s in self._states.items() if s == "active"]

    def load_config(self):
        with open(self.config_path, encoding="utf-8") as f:
            text = f.read()
        self._fingerprint = text
        for plugin in self._plugins.values():
            plugin.on_config_changed(json.loads(text).get(plugin.name, {}))

    def hot_reload(self):
        # TODO: 指纹相同返回 False,否则加载并对活跃插件热更新
        # 提示: 读文件原文,text == self._fingerprint 就 return False;self._fingerprint = text;
        #       遍历 self.active() 的名字,self._plugins[name].on_config_changed(json.loads(text).get(name, {}));
        #       return True
        raise NotImplementedError("t44-plugin-architecture-s5 尚未实现:请按 TODO 提示实现 hot_reload")

    def handle(self, text):
        if not self.bus.publish("request_in", text):
            print("  [runtime] 请求被否决,分发终止")
            return
        self.bus.publish("request_out", text)


def main():
    workdir = tempfile.mkdtemp()
    cfg_path = os.path.join(workdir, "plugins.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump({"echo": {"prefix": "raw"}}, f, ensure_ascii=False)
    rt = QiankunRuntime(cfg_path)
    for plugin in (EchoPlugin(), GuardPlugin()):
        rt.install(plugin)
        rt.activate(plugin.name)
    rt.load_config()
    for _ in range(3):
        rt.handle("你好,Agent 运行时底座")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump({"echo": {"prefix": "v2"}}, f, ensure_ascii=False)
    print(f"  热更新检测: {rt.hot_reload()}")
    rt.handle("你好,Agent 运行时底座")
    rt.handle("禁止飞行")


if __name__ == "__main__":
    main()
