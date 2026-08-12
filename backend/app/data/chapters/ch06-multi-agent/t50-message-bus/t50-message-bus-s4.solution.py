"""校园 AI 社 · s4:共享黑板 —— 成员们在同一块板上协作。"""
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
        return f"[{self.ts}] {self.author} 写入 {self.key} -> {self.value} (v{self.version})"


class Blackboard:
    """多 Agent 共享的黑板:数据 + 版本号 + 完整写入历史。"""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._versions: dict[str, int] = {}
        self.history: list[BoardEntry] = []

    def write(self, key: str, value: Any, author: str = "unknown") -> BoardEntry:
        """写入黑板:版本号 +1,记录历史,返回本次写入的流水。"""
        new_version = self._versions.get(key, 0) + 1
        self._data[key] = value
        self._versions[key] = new_version
        entry = BoardEntry(author=author, key=key, value=value, version=new_version)
        self.history.append(entry)
        return entry

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
