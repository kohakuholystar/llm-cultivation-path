"""校园 AI 社 · s2:发布订阅总线 —— 消息不再直达,交给总线分发。"""


# === 学习契约（面向学生）===
# 本节目标：发布订阅总线:消息交给总线分发。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `_next_id() -> int`：输入为签名中的参数；输出为 `int`。用途：按本节调用链完成对应处理
#   - `_now() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `log_handler(msg: Message) -> None`：输入为签名中的参数；输出为 `None`。用途：通用日志订阅者:收到任何消息都打印一行。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Message`：承载本节状态/数据；重点方法：to_dict。
#   - `MessageBus`：承载本节状态/数据；重点方法：subscribe, publish, topics。
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import itertools
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

_ID_GEN = itertools.count(1)


def _next_id() -> int:
    return next(_ID_GEN)


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Message:
    """与 s1 相同:一条 Agent 消息。"""

    sender: str
    topic: str
    payload: dict
    receiver: str = "*"
    msg_id: int = field(default_factory=_next_id)
    ts: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "msg_id": self.msg_id,
            "ts": self.ts,
            "sender": self.sender,
            "receiver": self.receiver,
            "topic": self.topic,
            "payload": self.payload,
        }

    def __str__(self) -> str:
        return f"[{self.ts}] {self.sender} -> {self.receiver} <{self.topic}> {self.payload}"


class MessageBus:
    """按主题分发消息的发布订阅总线。"""

    def __init__(self) -> None:
        self._subs: dict[str, list[Callable]] = defaultdict(list)
        self.published: list[Message] = []

    def subscribe(self, topic: str, handler: Callable) -> None:
        # TODO: 把回调登记进该主题的订阅列表
        # 提示: self._subs[topic].append(handler)
        raise NotImplementedError("t50-message-bus-s2 尚未实现:请按 TODO 提示补齐 subscribe 注册回调")

    def publish(self, msg: Message) -> None:
        # TODO: 先审计入队,再按主题派发给所有订阅者
        # 提示: self.published.append(msg); 遍历 list(self._subs.items()),
        #       若 topic == msg.topic 则逐个调用 handler,try/except 隔离订阅者异常
        raise NotImplementedError("t50-message-bus-s2 尚未实现:请按 TODO 提示补齐 publish 分发")

    def topics(self) -> list[str]:
        return sorted(self._subs)


def log_handler(msg: Message) -> None:
    """通用日志订阅者:收到任何消息都打印一行。"""
    print(f"[日志] {msg}")


def main() -> None:
    bus = MessageBus()
    bus.subscribe("task.assign", log_handler)
    bus.subscribe("report.progress", log_handler)
    bus.publish(Message(sender="product_manager", topic="task.assign",
                        payload={"task": "实现登录页", "assignee": "dev_1"}))
    bus.publish(Message(sender="dev_1", topic="report.progress",
                        payload={"task": "实现登录页", "percent": 60}))
    bus.publish(Message(sender="ops_1", topic="alarm.critical",
                        payload={"service": "gateway", "latency": 3200}))
    print("== 总线审计:共发布 3 条消息 ==")
    for m in bus.published:
        print(f"#{m.msg_id} {m.topic} from {m.sender}")
    print(f"注册主题: {bus.topics()}")


if __name__ == "__main__":
    main()
