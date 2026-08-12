"""校园 AI 社 · s6:迷你校园 AI 社实战 —— 四路消息汇成一张作战黑板。"""
import itertools
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable

_ID_GEN = itertools.count(1)


def _next_id() -> int:
    return next(_ID_GEN)


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Message:
    """一条 Agent 消息:谁发的、发给谁、什么主题、什么内容。"""

    sender: str
    topic: str
    payload: dict
    receiver: str = "*"
    msg_id: int = field(default_factory=_next_id)
    ts: str = field(default_factory=_now)


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


class Blackboard:
    """精简版共享黑板:数据 + 写入历史,配合总线使用。"""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self.history: list[dict] = []

    def write(self, key: str, value: Any, author: str = "unknown") -> None:
        version = sum(1 for h in self.history if h["key"] == key) + 1
        self._data[key] = value
        self.history.append({"author": author, "key": key, "value": value, "version": version})

    def read(self, key: str) -> Any:
        return self._data.get(key)

    def keys(self) -> list[str]:
        return sorted(self._data)


def blackboard_bridge(bus: MessageBus, board: Blackboard) -> None:
    """把 task.# 系列消息统统沉淀到黑板:键是 task.{任务}.{事件},值是整条 payload。"""
    def handler(msg: Message) -> None:
        task = msg.payload.get("task")
        event = msg.topic.split(".")[-1]
        board.write(f"task.{task}.{event}", msg.payload, msg.sender)
    bus.subscribe("task.#", handler)


def qa_gate(bus: MessageBus, board: Blackboard) -> None:
    """质检官:进度 100% 且带 commit 的任务才放行,结果广播到总线。"""
    def handler(msg: Message) -> None:
        task = msg.payload.get("task")
        passed = msg.payload.get("percent") == 100 and bool(msg.payload.get("commit"))
        board.write(f"task.{task}.qa", "通过" if passed else "打回", "qa_1")
        bus.publish(Message(sender="qa_1", topic="task.accepted" if passed else "task.rejected",
                            payload={"task": task, "qa": "通过" if passed else "打回"}))
    bus.subscribe("task.done", handler)


def daily_report(bus: MessageBus, board: Blackboard) -> None:
    """收工日报:消息流水 + 主题统计 + 黑板快照。"""
    print("===== 校园 AI 社日报 =====")
    for m in bus.published:
        print(f"  #{m.msg_id} [{m.ts}] {m.sender} -> {m.topic} {m.payload}")
    stat = dict(Counter(m.topic for m in bus.published))
    print(f"主题统计: {stat}")
    print("黑板快照:")
    for k in board.keys():
        print(f"  {k} = {board.read(k)}")
    print("===== 日报结束 =====")


def main() -> None:
    bus = MessageBus()
    board = Blackboard()
    blackboard_bridge(bus, board)
    qa_gate(bus, board)
    bus.publish(Message(sender="product_manager", topic="task.assign", payload={"task": "实现登录页", "assignee": "dev_1"}))
    bus.publish(Message(sender="dev_1", topic="task.accept", payload={"task": "实现登录页"}))
    bus.publish(Message(sender="dev_1", topic="task.progress", payload={"task": "实现登录页", "percent": 50}))
    bus.publish(Message(sender="dev_1", topic="task.done", payload={"task": "实现登录页", "percent": 100, "commit": "abc123"}))
    daily_report(bus, board)


if __name__ == "__main__":
    main()
