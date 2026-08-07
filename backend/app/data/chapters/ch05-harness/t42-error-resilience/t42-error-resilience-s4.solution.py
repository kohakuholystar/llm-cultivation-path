"""乾坤圈 · s4:幂等执行 IdempotentExecutor

网络重试会让同一请求被执行多次,幂等执行按 request_id 去重:
命中历史记录直接重放,首次执行成功才存档——失败不落库,允许重试。
"""
import threading
import time


class CircuitOpenError(RuntimeError):
    """熔断器处于 open 状态时抛出的快速失败异常。"""


class CircuitBreaker:
    """三态熔断器:closed -> open -> half_open -> closed(本步无打印)。"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold=3, cooldown=1.0,
                 success_threshold=1, now=time.monotonic):
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self.success_threshold = success_threshold
        self._now = now
        self.failures = 0
        self.successes = 0
        self.opened_at = None

    @property
    def state(self):
        if self.opened_at is None:
            return self.CLOSED
        if self._now() - self.opened_at < self.cooldown:
            return self.OPEN
        return self.HALF_OPEN

    def call(self, func, *args, **kwargs):
        if self.state is self.OPEN:
            raise CircuitOpenError("熔断中,直接快速失败")
        try:
            data = func(*args, **kwargs)
        except Exception:
            if self.state is self.HALF_OPEN:
                self.opened_at = self._now()
            else:
                self.failures += 1
                if self.failures >= self.failure_threshold:
                    self.opened_at = self._now()
            raise
        else:
            if self.state is self.HALF_OPEN:
                self.successes += 1
                if self.successes >= self.success_threshold:
                    self.opened_at = None
                    self.failures = 0
                    self.successes = 0
            else:
                self.failures = 0
            return data


class IdempotentExecutor:
    """按 request_id 去重:命中重放,首次执行成功才存档(失败不落库)。"""

    def __init__(self, registry=None):
        self.registry = dict(registry or {})
        self.lock = threading.Lock()

    def execute(self, request_id, func, *args, **kwargs):
        with self.lock:
            if request_id in self.registry:
                print(f"[幂等] 请求 {request_id} 命中历史记录,直接重放")
                return self.registry[request_id]
            print(f"[幂等] 请求 {request_id} 首次到达,开始执行")
            result = func(*args, **kwargs)
            # 失败不落库,允许重试
            self.registry[request_id] = result
            print(f"[幂等] 请求 {request_id} 执行成功,结果已存档")
            return result


def main():
    print("== 乾坤圈 · s4:幂等执行 IdempotentExecutor ==")
    breaker = CircuitBreaker(failure_threshold=2, cooldown=0.5)
    payment = {"balance": 100}

    def charge(amount):
        if payment["balance"] < amount:
            raise ValueError("余额不足")
        payment["balance"] -= amount
        return f"扣款成功,余额 {payment['balance']} 元"

    def guarded_charge(amount):
        return breaker.call(charge, amount)

    executor = IdempotentExecutor()
    for rid in ["pay-1001", "pay-1001", "pay-1002"]:
        print(f"  [{rid}] -> {executor.execute(rid, guarded_charge, 30)}")
    print(f"  余额:{payment['balance']} 元(pay-1001 只真正扣款一次)")

    try:
        executor.execute("pay-1003", guarded_charge, 999)
    except ValueError as exc:
        print(f"  [pay-1003] 失败:{exc}(未存档,可重试)")
    print(f"  [pay-1003] 重试 -> {executor.execute('pay-1003', guarded_charge, 10)}")


if __name__ == "__main__":
    main()
