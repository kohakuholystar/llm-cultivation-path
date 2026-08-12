"""Agent 运行时底座 · s2:降级链 FallbackChain

主路失败走备路,备路失败落兜底。本步实现降级链 FallbackChain:
按优先级逐个尝试策略,任一环节成功即返回,全部失败才抛出异常。
"""


# === 学习契约（面向学生）===
# 本节目标：降级链:主路不通走备路。完成后能把本节概念放入可运行的工程链路。
# 需要补写：strategy、retry_call、_；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `compute_backoff(attempt, base_delay=0.1, max_delay=2.0) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：返回第 attempt 次重试的等待时长(秒),指数增长并封顶。
#   - `retry_call(func, args=(), kwargs=None, retries=3, base_delay=0.1, max_delay=2.0, sleep=time.sleep) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按指数退避重试 func;重试次数用尽后抛出最后一次异常。
#   - `main() -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `FallbackChain`：承载本节状态/数据；重点方法：run。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import time


def compute_backoff(attempt, base_delay=0.1, max_delay=2.0):
    """返回第 attempt 次重试的等待时长(秒),指数增长并封顶。"""
    return min(base_delay * (2 ** attempt), max_delay)


def retry_call(func, args=(), kwargs=None, retries=3, base_delay=0.1,
               max_delay=2.0, sleep=time.sleep):
    """按指数退避重试 func;重试次数用尽后抛出最后一次异常。"""
    kwargs = dict(kwargs or {})
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt >= retries:
                break
            sleep(compute_backoff(attempt, base_delay, max_delay))
    raise last_exc


class FallbackChain:
    """按优先级顺序尝试多个策略,第一个成功的结果即为输出。

    用法:chain = FallbackChain([primary, backup, fallback]);
    调用 chain.run(*args) 依次尝试,成功即停,全部失败抛 RuntimeError。
    """

    def __init__(self, strategies):
        self.strategies = list(strategies)

    def run(self, *args, **kwargs):
        for idx, strategy in enumerate(self.strategies):
            name = getattr(strategy, "__name__", f"环节{idx}")
            print(f"[降级链] 环节 {idx}({name}) 开始尝试")
            # TODO: 用 try/except 包住 strategy(*args, **kwargs)
            # TODO: 成功时打印成功信息,并返回 {"ok": True, "source": name, "data": data}
            # TODO: 失败时打印失败原因,继续尝试下一环
            # 提示: try: data = strategy(*args, **kwargs);
            #       print(f"[降级链] 环节 {idx}({name}) 成功,停止降级");
            #       return {"ok": True, "source": name, "data": data}
            #       except Exception as exc:
            #       print(f"[降级链] 环节 {idx}({name}) 失败:{type(exc).__name__}: {exc}")
            raise NotImplementedError("FallbackChain.run 尚未实现:请按 TODO 提示补全降级尝试")
        raise RuntimeError("降级链全部环节失败,兜底策略必须写在链尾且不抛异常")


def main():
    print("== Agent 运行时底座 · s2:降级链 FallbackChain ==")

    def primary_llm(text):
        raise TimeoutError("旗舰模型上游超时")

    def backup_llm(text):
        raise TimeoutError("轻量模型上游超时")

    def rule_fallback(text):
        return f"【兜底】「{text}」暂时无法处理,请稍后再试"

    def with_retry(fn):
        def wrapper(*args):
            # TODO: 在 wrapper 内调用 retry_call(fn, args, retries=1, base_delay=0.01,
            # TODO:   max_delay=0.02, sleep=lambda _: None) 并返回结果
            # 提示: return retry_call(fn, args, retries=1, base_delay=0.01,
            #        max_delay=0.02, sleep=lambda _: None)
            raise NotImplementedError("wrapper 尚未实现:请按 TODO 提示完成重试包装")
        wrapper.__name__ = fn.__name__
        return wrapper

    chain = FallbackChain([with_retry(primary_llm), with_retry(backup_llm), rule_fallback])
    envelope = chain.run("查询天气")
    print(f"  成功来源:{envelope['source']}")
    print(f"  返回结果:{envelope['data']}")


if __name__ == "__main__":
    main()
