"""校园 AI 社 · s1:消息协议 —— Agent 之间说什么语言。"""
import itertools
import time
from dataclasses import dataclass, field

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

    def to_dict(self) -> dict:
        """把消息转成普通字典,方便落库、审计与序列化。"""
        return {
            "msg_id": self.msg_id,
            "ts": self.ts,
            "sender": self.sender,
            "receiver": self.receiver,
            "topic": self.topic,
            "payload": self.payload,
        }

    def __str__(self) -> str:
        """人类可读的消息摘要,日志与调试都靠它。"""
        return f"[{self.ts}] {self.sender} -> {self.receiver} <{self.topic}> {self.payload}"


def make_messages() -> list[Message]:
    """模拟校园 AI 社一天里的三条消息:任务分派、进度汇报、系统告警。"""
    return [
        Message(sender="product_manager", topic="task.assign",
                payload={"task": "实现登录页", "assignee": "dev_1"}),
        Message(sender="dev_1", topic="report.progress",
                payload={"task": "实现登录页", "percent": 60}),
        Message(sender="ops_1", topic="alarm.critical",
                payload={"service": "gateway", "latency": 3200}),
    ]


def main() -> None:
    for msg in make_messages():
        print(msg)
    print("== 序列化为字典 ==")
    for msg in make_messages():
        for key, value in msg.to_dict().items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
