"""Agent 运行时底座 · s5:韧性运行时 ResilientRunner

四层护甲合体:幂等(最外) -> 熔断 -> 降级链(内含重试)。
ResilientRunner 把前三步的组件拼成一条完整流水线,让 Agent
在重试、熔断、降级全部到位后仍保持幂等,重复请求不再重复伤害。
"""
import time


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
            sleep(min(base_delay * (2 ** attempt), max_delay))
    raise last_exc


class CircuitOpenError(RuntimeError):
    """熔断器处于 open 状态时抛出的快速失败异常。"""


class CircuitBreaker:
    """精简熔断器:失败达阈值跳闸,冷却后放行,成功即复位。"""

    def __init__(self, failure_threshold=3, cooldown=1.0, now=time.monotonic):
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self._now = now
        self.failures = 0
        self.opened_at = None

    def call(self, func, *args, **kwargs):
        if self.opened_at is not None:
            if self._now() - self.opened_at < self.cooldown:
                raise CircuitOpenError("熔断中,直接快速失败")
            self.opened_at = None
        try:
            data = func(*args, **kwargs)
        except Exception:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.opened_at = self._now()
            raise
        else:
            self.failures = 0
            return data


class FallbackChain:
    """按优先级逐个尝试策略,第一个成功的结果即为输出。"""

    def __init__(self, strategies):
        self.strategies = list(strategies)

    def run(self, *args, **kwargs):
        for idx, strategy in enumerate(self.strategies):
            name = getattr(strategy, "__name__", f"环节{idx}")
            try:
                data = strategy(*args, **kwargs)
                return {"ok": True, "source": name, "data": data}
            except Exception as exc:
                print(f"    [链] 环节 {idx}({name}) 失败:{type(exc).__name__}")
        raise RuntimeError("降级链全部环节失败,兜底策略必须写在链尾且不抛异常")


class IdempotentExecutor:
    """按 request_id 去重:命中重放,首次执行成功才存档。"""

    def __init__(self, registry=None):
        self.registry = dict(registry or {})

    def execute(self, request_id, func, *args, **kwargs):
        if request_id in self.registry:
            print(f"[幂等] 请求 {request_id} 命中历史记录,直接重放")
            return self.registry[request_id]
        print(f"[幂等] 请求 {request_id} 首次到达,开始执行")
        result = func(*args, **kwargs)
        self.registry[request_id] = result
        print(f"[幂等] 请求 {request_id} 执行成功,结果已存档")
        return result


class ResilientRunner:
    """韧性运行时:幂等(最外) -> 熔断 -> 降级链(内含重试)。"""

    def __init__(self, strategies, registry=None, failure_threshold=3,
                 cooldown=1.0):
        self.executor = IdempotentExecutor(registry)
        self.breaker = CircuitBreaker(failure_threshold, cooldown)
        self.chain = FallbackChain(strategies)

    def run(self, request_id, task):
        return self.executor.execute(
            request_id,
            lambda: self.breaker.call(lambda: self.chain.run(task)["data"]),
        )


def main():
    print("== Agent 运行时底座 · s5:韧性运行时 ResilientRunner ==")
    state = {"calls": 0}

    def llm_gateway(prompt):
        state["calls"] += 1
        if state["calls"] <= 2:
            raise TimeoutError("LLM 网关超时")
        return f"模型回答:{prompt}"

    def rule_fallback(prompt):
        return f"【兜底】规则回答:{prompt}"

    def with_retry(fn):
        def wrapper(prompt):
            return retry_call(fn, (prompt,), retries=1, sleep=lambda _: None)
        wrapper.__name__ = fn.__name__
        return wrapper

    runner = ResilientRunner([with_retry(llm_gateway), rule_fallback])
    for rid, task in [("r-1", "写一首诗"), ("r-1", "写一首诗"), ("r-2", "查天气")]:
        print(f"[agent] 结果:{runner.run(rid, task)}")
    print(f"[agent] LLM 实际调用 {state['calls']} 次(r-1 重放未重复调用)")


if __name__ == "__main__":
    main()
