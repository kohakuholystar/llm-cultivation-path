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
        # TODO: 新建 span 挂进树,并把 current 指向新 span
        # 提示: parent = self.current;span = {"name": name, "children": [], "started_at": time.perf_counter()};
        #       父为空挂进 self.roots,否则挂进 parent["children"];span["parent"] = parent;
        #       self.current = span;最后 self.log("info", "span.start", span=name)
        raise NotImplementedError("t43-observability-s2 尚未实现:请按 TODO 提示实现 start_span")

    def end_span(self) -> None:
        # TODO: 结算当前 span 的耗时并回退 current
        # 提示: 用 time.perf_counter() 差算 duration_ms(round(..., 2)) 写入 span["duration_ms"];
        #       self.log("info", "span.end", span=span["name"], duration_ms=...);
        #       最后 self.current = span["parent"]
        raise NotImplementedError("t43-observability-s2 尚未实现:请按 TODO 提示实现 end_span")

    def run_turn(self, prompt: str) -> None:
        # TODO: 组织一次完整回合的链路
        # 提示: start_span("agent.turn") 后 info 一条 llm.request(带 model 与 prompt);
        #       依次 start_span("tool.query_stock")、start_span("tool.appraise"),
        #       各自 info 一条 tool.invoke(带 name 与 args)后 end_span;
        #       最后 end_span 收尾 agent.turn
        raise NotImplementedError("t43-observability-s2 尚未实现:请按 TODO 提示实现 run_turn")

    def render_tree(self, spans: list[dict], indent: str = "") -> None:
        for span in spans:
            print(f"{indent}{span['name']} {span.get('duration_ms', 0)}ms")
            self.render_tree(span["children"], indent + "  ")


def main() -> None:
    # TODO: 跑一次回合,渲染链路树并回放事件
    # 提示: ob = QiankunObserver(stream=sys.stdout);ob.run_turn("帮我查飞剑的行情");
    #       print("== 链路树 ==") 后 ob.render_tree(ob.roots);
    #       print("== 事件回放 ==") 逐条打印 level 与 event;最后 print("链路追踪就绪")
    raise NotImplementedError("t43-observability-s2 尚未实现:请按 TODO 提示完成 main 演示")


if __name__ == "__main__":
    main()
