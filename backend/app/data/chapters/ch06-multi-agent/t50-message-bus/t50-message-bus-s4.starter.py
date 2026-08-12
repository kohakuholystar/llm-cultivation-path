"""校园 AI 社 · s4:共享黑板 —— 成员们在同一块板上协作。"""


# === 学习契约（面向学生）===
# 本节目标：共享黑板:团队在同一块板上协作。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `_next_id() -> int`：输入为签名中的参数；输出为 `int`。用途：按本节调用链完成对应处理
#   - `_now() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `BoardEntry`：承载本节状态/数据；重点方法：见类定义。
#   - `Blackboard`：承载本节状态/数据；重点方法：write, read, version, snapshot, keys。
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import itertools
import time
from dataclasses import dataclass, field
from typing import Any

_ID_GEN = itertools.count(1)


def _next_id() -> int:
    return next(_ID_GEN)


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class BoardEntry:
    """一条写入流水:谁、何时、写了什么、第几版。"""

    author: str
    key: str
    value: Any
    version: int
    msg_id: int = field(default_factory=_next_id)
    ts: str = field(default_factory=_now)

    def __str__(self) -> str:
        """人类可读的写入摘要。"""
        # TODO: 返回一行写入流水摘要
        # 提示: return f"[{self.ts}] {self.author} 写入 {self.key} -> {self.value} (v{self.version})",不要 print
        raise NotImplementedError("t50-message-bus-s4 尚未实现:请按 TODO 提示补齐 BoardEntry.__str__ 返回流水")


class Blackboard:
    """多 Agent 共享的黑板:数据 + 版本号 + 完整写入历史。"""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._versions: dict[str, int] = {}
        self.history: list[BoardEntry] = []

    def write(self, key: str, value: Any, author: str = "unknown") -> BoardEntry:
        """写入黑板:版本号 +1,记录历史,返回本次写入的流水。"""
        # TODO: 版本号自增,更新数据与版本表,构造流水追加进历史并返回
        # 提示: new_version = self._versions.get(key, 0) + 1;
        #       self._data[key] = value; self._versions[key] = new_version;
        #       entry = BoardEntry(author=author, key=key, value=value, version=new_version)
        #       self.history.append(entry); return entry
        raise NotImplementedError("t50-message-bus-s4 尚未实现:请按 TODO 提示补齐 write 写入")

    def read(self, key: str) -> Any:
        return self._data.get(key)

    def version(self, key: str) -> int:
        return self._versions.get(key, 0)

    def snapshot(self) -> dict[str, Any]:
        return dict(self._data)

    def keys(self) -> list[str]:
        return sorted(self._data)


def main() -> None:
    board = Blackboard()
    board.write("task.login.status", "doing", "dev_1")
    board.write("task.login.percent", 60, "dev_1")
    board.write("task.login.status", "review", "dev_1")
    print("== 黑板快照 ==")
    for k in board.keys():
        print(f"  {k} = {board.read(k)} (v{board.version(k)})")
    print("== 写入历史 ==")
    for entry in board.history:
        print(f"  {entry}")


if __name__ == "__main__":
    main()
