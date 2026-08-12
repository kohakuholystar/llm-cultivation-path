"""Agent 运行时底座 · s4:幂等执行 IdempotentExecutor

网络重试会让同一请求被执行多次,幂等执行按 request_id 去重:
命中历史记录直接重放,首次执行成功才存档——失败不落库,允许重试。
"""


# === 学习契约（面向学生）===
# 本节目标：幂等执行:重复请求不再重复伤害。完成后能把本节概念放入可运行的工程链路。
# 需要补写：func、ValueError；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `main() -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `CircuitOpenError`：承载本节状态/数据；重点方法：见类定义。
#   - `CircuitBreaker`：承载本节状态/数据；重点方法：state, call。
#   - `IdempotentExecutor`：承载本节状态/数据；重点方法：execute。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
        # TODO: 用 with self.lock 把「查重-执行-存档」包成原子操作
        # TODO: 先查 registry,命中就直接打印重放信息并 return 存档结果
        # TODO: 未命中则打印首次到达信息,执行 func(*args, **kwargs)
        # TODO: 执行成功后把结果存入 registry 并打印存档信息;失败不落库
        # 提示: with self.lock: 命中时 print 并 return self.registry[request_id];
        #       未命中 print 后 result = func(*args, **kwargs),写回 registry 再 return
        raise NotImplementedError("IdempotentExecutor.execute 尚未实现:请按 TODO 提示补全幂等逻辑")


def main():
    print("== Agent 运行时底座 · s4:幂等执行 IdempotentExecutor ==")
    breaker = CircuitBreaker(failure_threshold=2, cooldown=0.5)
    payment = {"balance": 100}

    def charge(amount):
        # TODO: 余额不足时 raise ValueError("余额不足")
        # TODO: 否则扣减余额并返回 f"扣款成功,余额 {payment['balance']} 元"
        # 提示: if payment["balance"] < amount: raise ValueError("余额不足");
        #       payment["balance"] -= amount;
        #       return f"扣款成功,余额 {payment['balance']} 元"
        raise NotImplementedError("charge 尚未实现:请按 TODO 提示补全扣款逻辑")

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
