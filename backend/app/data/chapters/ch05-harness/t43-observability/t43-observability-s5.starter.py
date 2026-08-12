"""运行时观测台 · s5:总装,观测与业务合一

前面的砖块都齐了,本步把它们砌成一座可复用的观测台:
一次回合有 span、有计数、有成败打点,收尾自动出报告——观测与业务合一。
"""


# === 学习契约（面向学生）===
# 本节目标：总装:观测与业务合一。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `QiankunObserver`：承载本节状态/数据；重点方法：log, info, warn, error, seen_events, start_span, end_span, inc, snapshot, generate_report, _report_span, save_report, run_agent_session。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
        # TODO: 用可观测的方式跑完一批提示词
        # 提示: ok = fail = 0,循环遍历 prompts;每个回合 start_span("agent.turn") +
        #       info("llm.request", model="deepseek-v4-pro", prompt=prompt);
        #       try 里含 "炸" 就 raise ValueError("关键词「炸」不合法"):
        #       成功 ok += 1、inc("tool.success")、打印查询完成;
        #       失败 fail += 1、inc("tool.error")、error("tool.failed", prompt=..., error=...)、打印查询失败;
        #       每回合都 inc("turns.completed") 并 end_span;收尾 info("agent.finish", rounds=2, ok=ok, fail=fail),
        #       打印观测总览与 save_report("观测报告.md") 路径
        raise NotImplementedError("t43-observability-s5 尚未实现:请按 TODO 提示实现 run_agent_session")


def main() -> None:
    # TODO: 创建观测者并跑一轮总装
    # 提示: ob = QiankunObserver(stream=sys.stdout);ob.run_agent_session(["帮我查展示素材的行情", "炸"])
    raise NotImplementedError("t43-observability-s5 尚未实现:请按 TODO 提示完成 main 演示")


if __name__ == "__main__":
    main()
