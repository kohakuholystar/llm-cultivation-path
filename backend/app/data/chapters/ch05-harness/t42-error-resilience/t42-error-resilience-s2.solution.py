"""乾坤圈 · s2:降级链 FallbackChain

主路失败走备路,备路失败落兜底。本步实现降级链 FallbackChain:
按优先级逐个尝试策略,任一环节成功即返回,全部失败才抛出异常。
"""
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
            try:
                data = strategy(*args, **kwargs)
                print(f"[降级链] 环节 {idx}({name}) 成功,停止降级")
                return {"ok": True, "source": name, "data": data}
            except Exception as exc:
                print(f"[降级链] 环节 {idx}({name}) 失败:{type(exc).__name__}: {exc}")
        raise RuntimeError("降级链全部环节失败,兜底策略必须写在链尾且不抛异常")


def main():
    print("== 乾坤圈 · s2:降级链 FallbackChain ==")

    def primary_llm(text):
        raise TimeoutError("旗舰模型上游超时")

    def backup_llm(text):
        raise TimeoutError("轻量模型上游超时")

    def rule_fallback(text):
        return f"【兜底】「{text}」暂时无法处理,请稍后再试"

    def with_retry(fn):
        def wrapper(*args):
            return retry_call(fn, args, retries=1, base_delay=0.01,
                              max_delay=0.02, sleep=lambda _: None)
        wrapper.__name__ = fn.__name__
        return wrapper

    chain = FallbackChain([with_retry(primary_llm), with_retry(backup_llm), rule_fallback])
    envelope = chain.run("查询天气")
    print(f"  成功来源:{envelope['source']}")
    print(f"  返回结果:{envelope['data']}")


if __name__ == "__main__":
    main()
