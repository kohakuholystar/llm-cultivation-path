"""乾坤观测台 · s1:结构化日志,JSON Lines 记心法

可观测性的第一块基石是日志。本步打造观测者 QiankunObserver 的雏形:
事件不再是随手 print 的散沙,而是一条条 JSON Lines——机器可读、可检索、可回放。
"""
import json
import sys


class QiankunObserver:
    """观测者:把散乱的事件整理成结构化日志(JSON Lines)。"""

    def __init__(self, stream=None) -> None:
        self.records = []
        self.stream = stream

    def log(self, level: str, event: str, **fields) -> None:
        record = {"level": level, "event": event}
        record.update(fields)
        self.records.append(record)
        self.stream.write(json.dumps(record, ensure_ascii=False) + "\n")

    def info(self, event: str, **fields) -> None:
        self.log("info", event, **fields)

    def warn(self, event: str, **fields) -> None:
        self.log("warn", event, **fields)

    def error(self, event: str, **fields) -> None:
        self.log("error", event, **fields)

    def seen_events(self) -> list[str]:
        seen = set()
        for r in self.records:
            seen.add(r["event"])
        return list(seen)

    def level_distribution(self) -> dict:
        dist = {}
        for r in self.records:
            dist[r["level"]] = dist.get(r["level"], 0) + 1
        return dist


def main() -> None:
    ob = QiankunObserver(stream=sys.stdout)
    ob.info("agent.start", model="deepseek-v4-pro", rounds=1)
    ob.warn("llm.slow", model="deepseek-v4-pro", latency_ms=3452)
    ob.error("llm.error", model="deepseek-v4-pro", kind="RateLimit", retryable=True)
    print("== 原始日志(JSON Lines)==")
    for r in ob.records:
        print(json.dumps(r, ensure_ascii=False))
    print("== 事件回放 ==")
    for r in ob.records:
        print("  ", r["level"], r["event"])
    print("== 事件种类 ==")
    for name in ob.seen_events():
        print("  -", name)
    print("== 级别分布 ==")
    for level, count in ob.level_distribution().items():
        print("  ", level, count)
    print("结构化日志就绪")


if __name__ == "__main__":
    main()
