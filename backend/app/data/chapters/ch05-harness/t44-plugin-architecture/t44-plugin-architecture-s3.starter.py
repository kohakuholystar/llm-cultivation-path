"""乾坤圈 · s3:钩子系统

插件之间不互相点名,而是向事件总线注册钩子。运行时发布事件,
插件按钩子表决定听不听、怎么听。getattr 反射分发,
`is False` 精确识别否决——插件第一次有了「说不」的能力。
"""
from abc import ABC, abstractmethod


class Plugin(ABC):
    def __init__(self, name, version, description):
        self.name = name
        self.version = version
        self.description = description

    def run(self, event, text):
        return "(无处理)"

    @abstractmethod
    def hooks(self):
        """返回 {事件名: 处理方法名} 的钩子表。"""


class EchoPlugin(Plugin):
    def hooks(self):
        return {"request_in": "run"}

    def run(self, event, text):
        print(f"  [echo] {text}")
        return f"[echo] {text}"


class LogPlugin(Plugin):
    def hooks(self):
        return {"request_in": "handle", "request_out": "handle"}

    def handle(self, event, text):
        print(f"  [log] 捕获事件 {event}: {text}")


class BlockPlugin(Plugin):
    def hooks(self):
        return {"request_in": "guard"}

    def guard(self, event, text):
        if "禁" in text:
            print("  [block] 检测到违禁内容,否决请求")
            return False
        return None


class HookBus:
    def __init__(self):
        self._subs = {}

    def subscribe(self, event, plugin):
        # TODO: 维护订阅表:只收会听该事件的插件,且不重复
        # 提示: event not in plugin.hooks() 直接 return;否则 setdefault(event, []) 建列表,
        #       判重(plugin not in 列表)后 append
        raise NotImplementedError("t44-plugin-architecture-s3 尚未实现:请按 TODO 提示实现 subscribe")

    def publish(self, event, text):
        # TODO: 逐位分发,结果 is False 时打印否决并终止
        # 提示: 遍历 self._subs.get(event, []);handler = getattr(plugin, plugin.hooks()[event]);
        #       result = handler(event, text);result is False 时
        #       print(f"  [hook] {plugin.name} 否决了事件 {event},分发终止") 并 return False;
        #       全部通过后 return True
        raise NotImplementedError("t44-plugin-architecture-s3 尚未实现:请按 TODO 提示实现 publish")

    def counts(self):
        return {event: len(subs) for event, subs in self._subs.items()}


class HookRuntime:
    def __init__(self, plugins):
        self.bus = HookBus()
        for plugin in plugins:
            for event in ("request_in", "request_out"):
                self.bus.subscribe(event, plugin)

    def handle(self, text):
        if not self.bus.publish("request_in", text):
            print("  请求被插件否决,分发终止")
            return
        self.bus.publish("request_out", text)
        print("  请求处理完毕")


def main():
    plugins = [
        EchoPlugin("echo", "1.0.0", "回声通道"),
        LogPlugin("log", "1.0.0", "访问日志"),
        BlockPlugin("block", "1.0.0", "内容安检"),
    ]
    rt = HookRuntime(plugins)
    counts = rt.bus.counts()
    print(f"订阅情况: request_in={counts.get('request_in', 0)} request_out={counts.get('request_out', 0)}")
    print("--- 正常请求 ---")
    rt.handle("你好,乾坤圈")
    print("--- 违规请求 ---")
    rt.handle("这个请求禁止执行")


if __name__ == "__main__":
    main()
