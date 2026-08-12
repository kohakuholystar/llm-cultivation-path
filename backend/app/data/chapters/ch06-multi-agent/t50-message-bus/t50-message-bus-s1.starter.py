"""校园 AI 社 · s1:消息协议 —— Agent 之间说什么语言。"""


# === 学习契约（面向学生）===
# 本节目标：消息协议:Agent 的第一门共同语言。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `_next_id() -> int`：输入为签名中的参数；输出为 `int`。用途：按本节调用链完成对应处理
#   - `_now() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `make_messages() -> list[Message]`：输入为签名中的参数；输出为 `list[Message]`。用途：模拟校园 AI 社一天里的三条消息:任务分派、进度汇报、系统告警。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Message`：承载本节状态/数据；重点方法：to_dict。
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
        # TODO: 返回含六键的字典,键名与字段一一对应
        # 提示: return {"msg_id": self.msg_id, "ts": ..., "sender": ..., "receiver": ..., "topic": ..., "payload": ...}
        raise NotImplementedError("t50-message-bus-s1 尚未实现:请按 TODO 提示补齐 to_dict 返回字典")

    def __str__(self) -> str:
        """人类可读的消息摘要,日志与调试都靠它。"""
        # TODO: 返回一行可读消息摘要
        # 提示: return f"[{self.ts}] {self.sender} -> {self.receiver} <{self.topic}> {self.payload}",不要 print
        raise NotImplementedError("t50-message-bus-s1 尚未实现:请按 TODO 提示补齐 __str__ 返回摘要")


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
