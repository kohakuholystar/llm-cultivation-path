"""天庭 · s2:发布订阅总线 —— 消息不再直达,交给总线分发。"""
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
        self._subs[topic].append(handler)

    def publish(self, msg: Message) -> None:
        self.published.append(msg)
        for topic, handlers in list(self._subs.items()):
            if topic != msg.topic:
                continue
            for handler in handlers:
                try:
                    handler(msg)
                except Exception as exc:
                    print(f"[总线] 订阅者异常: {exc}")

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
