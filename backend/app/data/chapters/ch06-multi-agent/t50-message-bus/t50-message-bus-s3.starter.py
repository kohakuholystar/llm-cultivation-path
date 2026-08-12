"""校园 AI 社 · s3:通配符订阅 —— 一个模式,收下一整类消息。"""


# === 学习契约（面向学生）===
# 本节目标：通配符订阅:一个模式收下一整类消息。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `_next_id() -> int`：输入为签名中的参数；输出为 `int`。用途：按本节调用链完成对应处理
#   - `_now() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `topic_match(pattern: str, topic: str) -> bool`：输入为签名中的参数；输出为 `bool`。用途：通配符匹配:* 恰好一层,# 匹配任意剩余层(可为空)。
#   - `report_handler(msg: Message) -> None`：输入为签名中的参数；输出为 `None`。用途：任务看板:展示任务相关消息。
#   - `alarm_handler(msg: Message) -> None`：输入为签名中的参数；输出为 `None`。用途：告警接收器:只关心告警内容。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Message`：承载本节状态/数据；重点方法：to_dict。
#   - `MessageBus`：承载本节状态/数据；重点方法：subscribe, publish, counts。
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
        # TODO: 把「(模式, 回调)」元组追加进订阅表
        # 提示: self._subs.append((pattern, handler))
        raise NotImplementedError("t50-message-bus-s3 尚未实现:请按 TODO 提示补齐 subscribe 注册模式订阅")

    def publish(self, msg: Message) -> None:
        # TODO: 先审计入队,再按通配模式匹配派发
        # 提示: 遍历 list(self._subs) 逐对取 pattern/handler,
        #       若 not topic_match(pattern, msg.topic) 则跳过,try/except 隔离订阅者异常
        raise NotImplementedError("t50-message-bus-s3 尚未实现:请按 TODO 提示补齐 publish 模式派发")

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
