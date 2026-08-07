"""天庭 · s5:总线驱动黑板 —— 消息流进来,黑板自己长出来。"""
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


def bridge_status(bus: MessageBus, board: Blackboard) -> None:
    """把 task.done 消息桥接成黑板上的完成状态。"""
    def handler(msg: Message) -> None:
        task = msg.payload.get("task")
        board.write(f"task.{task}.status", "done", msg.sender)
    bus.subscribe("task.done", handler)


def bridge_progress(bus: MessageBus, board: Blackboard) -> None:
    """把 task.progress 消息桥接成黑板上的进度百分比。"""
    def handler(msg: Message) -> None:
        task = msg.payload.get("task")
        percent = msg.payload.get("percent")
        board.write(f"task.{task}.percent", percent, msg.sender)
    bus.subscribe("task.progress", handler)


def topic_stats(bus: MessageBus) -> dict[str, int]:
    """按主题统计总线上各消息的条数。"""
    return dict(Counter(m.topic for m in bus.published))


def main() -> None:
    bus = MessageBus()
    board = Blackboard()
    bridge_status(bus, board)
    bridge_progress(bus, board)
    bus.publish(Message(sender="product_manager", topic="task.assign", payload={"task": "实现登录页", "assignee": "dev_1"}))
    bus.publish(Message(sender="dev_1", topic="task.progress", payload={"task": "实现登录页", "percent": 40}))
    bus.publish(Message(sender="dev_1", topic="task.done", payload={"task": "实现登录页", "percent": 100}))
    bus.publish(Message(sender="product_manager", topic="task.progress", payload={"task": "修复登录 bug", "percent": 10}))
    print("== 黑板最终状态 ==")
    for k in board.keys():
        print(f"  {k} = {board.read(k)}")
    print(f"== 总线共发布 4 条消息,黑板写入 {len(board.history)} 笔 ==")
    print(f"== 主题统计:{topic_stats(bus)} ==")


if __name__ == "__main__":
    main()
