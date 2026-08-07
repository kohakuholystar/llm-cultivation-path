"""乾坤圈 · s3:熔断器 CircuitBreaker

熔断器给故障装上闸门:连续失败达到阈值就跳闸(open),
冷却期内的调用直接快速失败,不再打必坏的依赖;冷却期结束
进入 half_open 试探,试探成功则恢复,失败则重新熔断。
"""
import time


class CircuitOpenError(RuntimeError):
    """熔断器处于 open 状态时抛出的快速失败异常。"""


class CircuitBreaker:
    """三态熔断器:closed -> open -> half_open -> closed。"""

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
                print("[熔断器] half_open 试探失败,重新熔断 -> open")
            else:
                self.failures += 1
                if self.failures >= self.failure_threshold:
                    self.opened_at = self._now()
                    print(f"[熔断器] 连续失败 {self.failures} 次,状态 -> open")
            raise
        else:
            if self.state is self.HALF_OPEN:
                self.successes += 1
                if self.successes >= self.success_threshold:
                    self.opened_at = None
                    self.failures = 0
                    self.successes = 0
                    print("[熔断器] 试探成功,状态 -> closed")
            else:
                self.failures = 0
            return data


class FakeClock:
    """可控时钟:手动 advance 时间,便于测试熔断器的冷却迁移。"""

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


def main():
    print("== 乾坤圈 · s3:熔断器 CircuitBreaker ==")
    clock = FakeClock()

    def fragile_service():
        raise ConnectionError("数据库连接被拒绝")

    breaker = CircuitBreaker(failure_threshold=2, cooldown=0.5,
                             success_threshold=1, now=clock)
    for i in range(1, 3):
        try:
            breaker.call(fragile_service)
        except ConnectionError as exc:
            print(f"[熔断器] 第 {i} 次失败:{exc}")
    print(f"[熔断器] 当前状态:{breaker.state}")

    def ask_primary():
        return breaker.call(fragile_service)

    def ask_fallback():
        return "【兜底】数据库开小差了,请稍后再试"

    try:
        ask_primary()
    except CircuitOpenError as exc:
        print(f"[降级] 主路快速失败:{exc}")
    print(f"[降级] 熔断期间的回答:{ask_fallback()}")

    clock.advance(0.6)
    print("[熔断器] 冷却期结束,进入 half_open 试探")
    print(f"[熔断器] 试探成功:{breaker.call(lambda: '数据库已恢复')}")
    print(f"[熔断器] 最终状态:{breaker.state}")


if __name__ == "__main__":
    main()
