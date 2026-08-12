"""运行时观测台 · s1:使用 logging 输出结构化日志。"""
import json
import logging
import sys


class JsonLineFormatter(logging.Formatter):
    """将 LogRecord 中的 event_fields 编码为一行 JSON。"""

    def format(self, record: logging.LogRecord) -> str:
        fields = getattr(record, "event_fields", {})
        payload = {"level": record.levelname.lower(), "event": record.msg, **fields}
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def configure_logger(stream) -> logging.Logger:
    """创建本练习独立 logger，避免污染根 logger。"""
    logger = logging.getLogger("harness.lesson")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLineFormatter())
    logger.addHandler(handler)
    return logger


def log_event(logger: logging.Logger, level: int, event: str, **fields) -> None:
    """以固定事件名和结构化字段写一条日志。"""
    logger.log(level, event, extra={"event_fields": fields})


def main() -> None:
    logger = configure_logger(sys.stdout)
    log_event(logger, logging.INFO, "agent.start", model="deepseek-v4-pro", request_id="demo-1")
    log_event(logger, logging.WARNING, "llm.slow", model="deepseek-v4-pro", latency_ms=3452)
    log_event(logger, logging.ERROR, "llm.error", error_kind="RateLimit", retryable=True)
    print("结构化日志就绪：使用 logging + JSON Lines")


if __name__ == "__main__":
    main()
