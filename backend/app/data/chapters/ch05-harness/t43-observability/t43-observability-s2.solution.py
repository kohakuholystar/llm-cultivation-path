"""乾坤观测台 · s2:链路追踪,span 树里见因果

上一刻钟我们让事件成了行行 JSON。本步再进一步:把事件串成调用链
——请求从哪来、经过了哪些工具、每段花了多久,都挂在一棵 span 树上。
"""
import json
import sys
import time


class QiankunObserver:
    """观测者:用 span 栈把事件串成带耗时的调用链树。"""

    def __init__(self, stream=None) -> None:
        self.records = []
        self.stream = stream
        self.roots = []
        self.current = None

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
        span["duration_ms"] = round((time.perf_counter() - span["started_at"]) * 1000, 2)
        self.log("info", "span.end", span=span["name"], duration_ms=span["duration_ms"])
        self.current = span["parent"]

    def run_turn(self, prompt: str) -> None:
        self.start_span("agent.turn")
        self.info("llm.request", model="deepseek-v4-pro", prompt=prompt)
        self.start_span("tool.query_stock")
        self.info("tool.invoke", name="query_stock", args={"keyword": "剑"})
        self.end_span()
        self.start_span("tool.appraise")
        self.info("tool.invoke", name="appraise", args={"item_name": "飞剑"})
        self.end_span()
        self.end_span()

    def render_tree(self, spans: list[dict], indent: str = "") -> None:
        for span in spans:
            print(f"{indent}{span['name']} {span.get('duration_ms', 0)}ms")
            self.render_tree(span["children"], indent + "  ")


def main() -> None:
    ob = QiankunObserver(stream=sys.stdout)
    ob.run_turn("帮我查飞剑的行情")
    print("== 链路树 ==")
    ob.render_tree(ob.roots)
    print("== 事件回放 ==")
    for r in ob.records:
        print("  ", r["level"], r["event"])
    print("链路追踪就绪")


if __name__ == "__main__":
    main()
