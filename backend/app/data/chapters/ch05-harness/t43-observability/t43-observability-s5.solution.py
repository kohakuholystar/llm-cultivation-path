"""乾坤观测台 · s5:总装,观测与业务合一

前面的砖块都齐了,本步把它们砌成一座可复用的观测台:
一次回合有 span、有计数、有成败打点,收尾自动出报告——观测与业务合一。
"""
import json
import sys
import time


class QiankunObserver:
    """观测者:可观测地跑完一批提示词,自动沉淀链路、指标与报告。"""

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
        lines = ["# 观测报告", "", "## 链路追踪"]
        for span in self.roots:
            self._report_span(lines, span, 0)
        lines.append("## 指标")
        for metric, value in self.counters.items():
            lines.append(f"- `{metric}`: {value}")
        for name, values in self.durations.items():
            lines.append(f"- `{name}`: {len(values)} 次,min {min(values)}ms,max {max(values)}ms")
        return "\n".join(lines) + "\n"

    def _report_span(self, lines: list[str], span: dict, depth: int) -> None:
        prefix = "  " * depth
        lines.append(f"- {prefix}`{span['name']}` {span.get('duration_ms', 0)}ms")
        for child in span["children"]:
            self._report_span(lines, child, depth + 1)

    def save_report(self, out_path: str) -> str:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(self.generate_report())
        return out_path

    def run_agent_session(self, prompts: list[str]) -> None:
        ok = fail = 0
        for prompt in prompts:
            self.start_span("agent.turn")
            self.info("llm.request", model="deepseek-v4-pro", prompt=prompt)
            try:
                if "炸" in prompt:
                    raise ValueError("关键词「炸」不合法")
                ok += 1
                self.inc("tool.success")
                print("查询完成: %s" % prompt)
            except ValueError as exc:
                fail += 1
                self.inc("tool.error")
                self.error("tool.failed", prompt=prompt, error=str(exc))
                print("查询失败: %s -> %s" % (prompt, exc))
            self.inc("turns.completed")
            self.end_span()
        self.info("agent.finish", rounds=2, ok=ok, fail=fail)
        print("== 观测总览:回合 %d,成功 %d,失败 %d ==" % (2, ok, fail))
        print("== 报告已写入:%s ==" % self.save_report("观测报告.md"))


def main() -> None:
    ob = QiankunObserver(stream=sys.stdout)
    ob.run_agent_session(["帮我查飞剑的行情", "炸"])


if __name__ == "__main__":
    main()
