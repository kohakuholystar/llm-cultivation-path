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
        # TODO: opened_at 为 None 时返回 CLOSED
        # TODO: 距 opened_at 不足 cooldown 时返回 OPEN
        # TODO: 否则冷却期已过,返回 HALF_OPEN
        # 提示: if self.opened_at is None: return self.CLOSED;
        #       if self._now() - self.opened_at < self.cooldown: return self.OPEN;
        #       return self.HALF_OPEN
        raise NotImplementedError("CircuitBreaker.state 尚未实现:请按 TODO 提示实现三态判定")

    def call(self, func, *args, **kwargs):
        if self.state is self.OPEN:
            raise CircuitOpenError("熔断中,直接快速失败")
        try:
            data = func(*args, **kwargs)
        except Exception:
            # TODO: half_open 态试探失败:把 opened_at 重置为当前时刻,打印重新熔断提示
            # TODO: closed 态连续失败:failures 加 1
            # TODO: failures 达到 failure_threshold 时,把 opened_at 置为当前时刻并打印跳闸提示
            # 提示: half_open 时 opened_at = self._now() 并打印「重新熔断」;
            #       closed 时 failures += 1,达阈值置 opened_at 并打印跳闸;raise 保留原样抛出
            raise NotImplementedError("CircuitBreaker.call 尚未实现:请按 TODO 提示补全失败迁移")
            raise
        else:
            # TODO: half_open 态试探成功:successes 加 1
            # TODO: successes 达到 success_threshold 时,复位 opened_at/failures/successes 并打印恢复提示
            # TODO: closed 态成功则清零 failures
            # 提示: half_open 时 successes += 1,达阈值复位三态并打印;closed 时 failures = 0;
            #       return data 保留
            raise NotImplementedError("CircuitBreaker.call 尚未实现:请按 TODO 提示补全成功恢复")
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
