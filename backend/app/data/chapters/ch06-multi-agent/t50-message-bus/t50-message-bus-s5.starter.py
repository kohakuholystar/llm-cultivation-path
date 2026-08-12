"""校园 AI 社 · s5:总线驱动黑板 —— 消息流进来,黑板自己长出来。"""


# === 学习契约（面向学生）===
# 本节目标：总线驱动黑板:消息自动沉淀为状态。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `_next_id() -> int`：输入为签名中的参数；输出为 `int`。用途：按本节调用链完成对应处理
#   - `_now() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `topic_match(pattern: str, topic: str) -> bool`：输入为签名中的参数；输出为 `bool`。用途：通配符匹配:* 恰好一层,# 匹配任意剩余层(可为空)。
#   - `bridge_status(bus: MessageBus, board: Blackboard) -> None`：输入为签名中的参数；输出为 `None`。用途：把 task.done 消息桥接成黑板上的完成状态。
#   - `bridge_progress(bus: MessageBus, board: Blackboard) -> None`：输入为签名中的参数；输出为 `None`。用途：把 task.progress 消息桥接成黑板上的进度百分比。
#   - `topic_stats(bus: MessageBus) -> dict[str, int]`：输入为签名中的参数；输出为 `dict[str, int]`。用途：按主题统计总线上各消息的条数。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Message`：承载本节状态/数据；重点方法：见类定义。
#   - `MessageBus`：承载本节状态/数据；重点方法：subscribe, publish。
#   - `Blackboard`：承载本节状态/数据；重点方法：write, read, keys。
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
    # TODO: 定义 handler 读 task/percent 写入黑板,再订阅 task.progress
    # 提示: def handler(msg): task = msg.payload.get("task"); percent = msg.payload.get("percent");
    #       board.write(f"task.{task}.percent", percent, msg.sender)
    #       bus.subscribe("task.progress", handler)
    raise NotImplementedError("t50-message-bus-s5 尚未实现:请按 TODO 提示补齐 bridge_progress 桥接")


def topic_stats(bus: MessageBus) -> dict[str, int]:
    """按主题统计总线上各消息的条数。"""
    # TODO: 用 Counter 统计 bus.published 中各消息主题的条数
    # 提示: return dict(Counter(m.topic for m in bus.published))
    raise NotImplementedError("t50-message-bus-s5 尚未实现:请按 TODO 提示补齐 topic_stats 统计")


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
