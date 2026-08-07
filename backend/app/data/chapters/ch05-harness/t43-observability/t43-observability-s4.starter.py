"""乾坤观测台 · s4:Markdown 报告,观测结果落成文

日志、链路、指标都在手了,还得能带走、能复盘。本步把观测者的家底
拼成一份 Markdown 报告:标题、链路树、指标小节,一页纸讲完全局。
"""
import json
import sys
import time


class QiankunObserver:
    """观测者:把日志、链路与指标沉淀成 Markdown 报告。"""

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

    def generate_report(self) -> str:
        # TODO: 拼出整份 Markdown 报告
        # 提示: lines = ["# 观测报告", "", "## 链路追踪"];遍历 self.roots 调 _report_span(lines, span, 0);
        #       补 "## 指标",counters 渲染成 "- `{metric}`: {value}",durations 渲染成
        #       "- `{name}`: {len} 次,min {min}ms,max {max}ms";最后 "\n".join(lines) + "\n" 返回
        raise NotImplementedError("t43-observability-s4 尚未实现:请按 TODO 提示实现 generate_report")

    def _report_span(self, lines: list[str], span: dict, depth: int) -> None:
        # TODO: 把一个 span 渲染成一行并递归子树
        # 提示: prefix = "  " * depth;lines.append(f"- {prefix}`{span['name']}` {span.get('duration_ms', 0)}ms");
        #       再对 span["children"] 递归 _report_span(lines, child, depth + 1)
        raise NotImplementedError("t43-observability-s4 尚未实现:请按 TODO 提示实现 _report_span")

    def save_report(self, out_path: str) -> str:
        # TODO: 把报告全文写盘并返回路径
        # 提示: with open(out_path, "w", encoding="utf-8") as f: f.write(self.generate_report());
        #       然后 return out_path
        raise NotImplementedError("t43-observability-s4 尚未实现:请按 TODO 提示实现 save_report")


def main() -> None:
    # TODO: 组织一次带链路与指标的调用,保存报告并打印
    # 提示: ob = QiankunObserver(stream=sys.stdout);start_span("agent.turn") -> start_span("tool.query_stock")
    #       -> inc("tool.query_stock") -> end_span -> end_span,再 inc("llm.calls");
    #       path = ob.save_report("观测报告.md");print("报告已生成:%s" % path);print(ob.generate_report())
    raise NotImplementedError("t43-observability-s4 尚未实现:请按 TODO 提示完成 main 演示")


if __name__ == "__main__":
    main()
