"""运行时观测台 · s1:使用 logging 输出结构化日志。

不要把业务日志藏进自定义“观测者”类。本步直接使用 Python 标准库
logging：事件字段以 JSON Lines 写到标准输出，日志级别仍由 logging 管理。
"""


# === 学习契约（面向学生）===
# 本节目标：结构化日志:用 logging 输出 JSON Lines。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `configure_logger(stream) -> logging.Logger`：输入为签名中的参数；输出为 `logging.Logger`。用途：创建本练习独立 logger，避免污染根 logger。
#   - `log_event(logger: logging.Logger, level: int, event: str, **fields) -> None`：输入为签名中的参数；输出为 `None`。用途：以固定事件名和结构化字段写一条日志。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `JsonLineFormatter`：承载本节状态/数据；重点方法：format。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import json
import logging
import sys


class JsonLineFormatter(logging.Formatter):
    """将 LogRecord 中的 event_fields 编码为一行 JSON。"""

    def format(self, record: logging.LogRecord) -> str:
        # TODO: 取出 record.event_fields，补入 level、event，并 json.dumps 返回。
        # 提示: fields = getattr(record, "event_fields", {});
        #       payload = {"level": record.levelname.lower(), "event": record.msg, **fields}
        #       return json.dumps(payload, ensure_ascii=False, sort_keys=True)
        raise NotImplementedError("请实现 JsonLineFormatter.format")


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
    # TODO: 调用 logger.log，并通过 extra 传入 event_fields。
    # 提示: logger.log(level, event, extra={"event_fields": fields})
    raise NotImplementedError("请实现 log_event")


def main() -> None:
    logger = configure_logger(sys.stdout)
    # TODO: 依次记录 agent.start、llm.slow、llm.error 三条事件。
    # 提示: 使用 logging.INFO/WARNING/ERROR；字段不要包含 API Key 或完整提示词。
    raise NotImplementedError("请完成 main 演示")


if __name__ == "__main__":
    main()
