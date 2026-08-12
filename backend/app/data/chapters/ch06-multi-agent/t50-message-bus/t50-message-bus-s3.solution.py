"""校园 AI 社 · s3:通配符订阅 —— 一个模式,收下一整类消息。"""
import itertools
import time
from dataclasses import dataclass, field
from typing import Callable

_ID_GEN = itertools.count(1)


def _next_id() -> int:
    return next(_ID_GEN)


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Message:
    """与 s2 相同:一条 Agent 消息。"""

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


def topic_match(pattern: str, topic: str) -> bool:
    """通配符匹配:* 恰好一层,# 匹配任意剩余层(可为空)。"""
    p_parts = pattern.split(".")
    t_parts = topic.split(".")
    for i, p in enumerate(p_parts):
        if p == "#":
            return True
        if i >= len(t_parts):
            return False
        if p != "*" and p != t_parts[i]:
            return False
    return len(p_parts) == len(t_parts)


class MessageBus:
    """支持通配符订阅的发布订阅总线。"""

    def __init__(self) -> None:
        self._subs: list[tuple[str, Callable]] = []
        self.published: list[Message] = []

    def subscribe(self, pattern: str, handler: Callable) -> None:
        self._subs.append((pattern, handler))

    def publish(self, msg: Message) -> None:
        self.published.append(msg)
        for pattern, handler in list(self._subs):
            if not topic_match(pattern, msg.topic):
                continue
            try:
                handler(msg)
            except Exception as exc:
                print(f"[总线] 订阅者异常: {exc}")

    def counts(self) -> dict[str, int]:
        """按主题统计各收到了多少条消息。"""
        counter: dict[str, int] = {}
        for m in self.published:
            counter[m.topic] = counter.get(m.topic, 0) + 1
        return counter


def report_handler(msg: Message) -> None:
    """任务看板:展示任务相关消息。"""
    print(f"[看板] {msg.topic}: {msg.payload}")


def alarm_handler(msg: Message) -> None:
    """告警接收器:只关心告警内容。"""
    print(f"[告警] {msg.payload}")


def main() -> None:
    bus = MessageBus()
    bus.subscribe("task.*", report_handler)
    bus.subscribe("alarm.#", alarm_handler)
    bus.publish(Message(sender="product_manager", topic="task.assign",
                        payload={"task": "实现登录页", "assignee": "dev_1"}))
    bus.publish(Message(sender="dev_1", topic="task.done",
                        payload={"task": "实现登录页", "percent": 100}))
    bus.publish(Message(sender="product_manager", topic="task.assign",
                        payload={"task": "修复登录 bug", "assignee": "dev_1"}))
    bus.publish(Message(sender="ops_1", topic="alarm.critical",
                        payload={"service": "gateway", "latency": 3200}))
    print(f"== 统计:{bus.counts()} ==")


if __name__ == "__main__":
    main()
