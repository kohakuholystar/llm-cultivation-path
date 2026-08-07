"""乾坤观测台 · s3:指标统计,计数器与耗时桶

日志能讲因果,指标能见全局。本步给观测者装上报数能力:
调用次数用计数器累加,耗时按名字收进桶里,快照一打,全局数字一目了然。
"""
import json
import sys
import time


class QiankunObserver:
    """观测者:在事件与 span 之上,汇总计数器与耗时的指标快照。"""

    def __init__(self, stream=None) -> None:
        self.records = []
        self.stream = stream
        self.roots = []
        self.current = None
        self.counters = {}
        self.durations = {}

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

    def start_span(self, name: str) -> None:
        parent = self.current
        span = {"name": name, "children": [], "started_at": time.perf_counter()}
        (self.roots if parent is None else parent["children"]).append(span)
        span["parent"] = parent
        self.current = span
        self.log("info", "span.start", span=name)

    def end_span(self) -> None:
        span = self.current
        duration = round((time.perf_counter() - span["started_at"]) * 1000, 2)
        span["duration_ms"] = duration
        self.durations.setdefault(span["name"], []).append(duration)
        self.log("info", "span.end", span=span["name"], duration_ms=duration)
        self.current = span["parent"]

    def inc(self, metric: str, by: int = 1) -> None:
        self.counters[metric] = self.counters.get(metric, 0) + by

    def snapshot(self) -> dict:
        stats = {
            name: {"count": len(v), "min_ms": min(v), "max_ms": max(v), "sum_ms": sum(v)}
            for name, v in self.durations.items()
        }
        return {"counters": dict(self.counters), "durations": stats}


def main() -> None:
    ob = QiankunObserver(stream=sys.stdout)
    for _ in range(3):
        ob.inc("llm.calls")
    for ms in (20.0, 40.0, 60.0):
        ob.durations.setdefault("tool.duration", []).append(ms)
    snap = ob.snapshot()
    print("== 指标快照 ==")
    for metric, value in snap["counters"].items():
        print(f"  {metric}={value}")
    for name, stats in snap["durations"].items():
        print(f"  {name}: {stats['count']} 次,min {stats['min_ms']}ms,max {stats['max_ms']}ms")
    print("指标统计就绪")


if __name__ == "__main__":
    main()
