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
        # TODO: 把事件整理成一行 JSON Lines,追加进 records 并写入 stream
        # 提示: record = {"level": level, "event": event},record.update(fields);
        #       self.records.append(record),再 self.stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        raise NotImplementedError("t43-observability-s1 尚未实现:请按 TODO 提示实现 log")

    def info(self, event: str, **fields) -> None:
        self.log("info", event, **fields)

    def warn(self, event: str, **fields) -> None:
        self.log("warn", event, **fields)

    def error(self, event: str, **fields) -> None:
        self.log("error", event, **fields)

    def seen_events(self) -> list[str]:
        # TODO: 返回出现过的事件名列表(去重,顺序不限)
        # 提示: 遍历 self.records 收集 r["event"],用 set 去重后转 list
        raise NotImplementedError("t43-observability-s1 尚未实现:请按 TODO 提示实现 seen_events")

    def level_distribution(self) -> dict:
        # TODO: 统计各 level 的出现次数并返回 {"info": 1, "error": 1, ...}
        # 提示: 遍历 self.records,dist[r["level"]] = dist.get(r["level"], 0) + 1
        raise NotImplementedError("t43-observability-s1 尚未实现:请按 TODO 提示实现 level_distribution")


def main() -> None:
    ob = QiankunObserver(stream=sys.stdout)
    # TODO: 记录启动/缓慢/错误三条事件,再回放并统计
    # 提示: ob.info("agent.start", model="deepseek-v4-pro", rounds=1);
    #       ob.warn("llm.slow", model="deepseek-v4-pro", latency_ms=3452);
    #       ob.error("llm.error", model="deepseek-v4-pro", kind="RateLimit", retryable=True);
    #       依次打印原始日志(逐条 json.dumps 回放 records)、事件回放(level+event)、
    #       事件种类(seen_events)、级别分布(level_distribution),最后 print("结构化日志就绪")
    raise NotImplementedError("t43-observability-s1 尚未实现:请按 TODO 提示完成 main 演示")


if __name__ == "__main__":
    main()
