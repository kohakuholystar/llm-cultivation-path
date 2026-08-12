"""运行时观测台 · s3:指标统计,计数器与耗时桶

日志能讲因果,指标能见全局。本步给观测者装上报数能力:
调用次数用计数器累加,耗时按名字收进桶里,快照一打,全局数字一目了然。
"""


# === 学习契约（面向学生）===
# 本节目标：指标统计:计数器与耗时桶。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `QiankunObserver`：承载本节状态/数据；重点方法：log, info, warn, error, seen_events, start_span, end_span, inc, snapshot。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
        # TODO: 计数器累加,把结果写回 counters
        # 提示: self.counters[metric] = self.counters.get(metric, 0) + by
        raise NotImplementedError("t43-observability-s3 尚未实现:请按 TODO 提示实现 inc")

    def snapshot(self) -> dict:
        # TODO: 汇总一次指标快照并返回
        # 提示: 遍历 self.durations,为每个名字算 count/min_ms/max_ms/sum_ms(字典推导式);
        #       返回 {"counters": dict(self.counters), "durations": stats}
        raise NotImplementedError("t43-observability-s3 尚未实现:请按 TODO 提示实现 snapshot")


def main() -> None:
    # TODO: 造计数与耗时样本,打快照并打印
    # 提示: ob = QiankunObserver(stream=sys.stdout);循环 3 次 ob.inc("llm.calls");
    #       用 ob.durations.setdefault("tool.duration", []).append(ms) 喂 20.0/40.0/60.0;
    #       snap = ob.snapshot() 后打印 "== 指标快照 =="、各计数器与耗时统计,最后 print("指标统计就绪")
    raise NotImplementedError("t43-observability-s3 尚未实现:请按 TODO 提示完成 main 演示")


if __name__ == "__main__":
    main()
