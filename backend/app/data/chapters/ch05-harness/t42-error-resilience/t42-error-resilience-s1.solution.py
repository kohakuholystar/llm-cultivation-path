"""Agent 运行时底座 · s1:指数退避重试

本步为「Agent 运行时底座」运行时装上第一层护甲:指数退避重试。
compute_backoff 负责计算每次重试前的等待时长,retry_call
负责在函数调用失败后按该节奏自动重试,并放行不可重试的异常。
"""
import time


def compute_backoff(attempt, base_delay=0.1, max_delay=2.0, jitter=0.0):
    """计算第 attempt 次重试前的等待时长(秒),指数增长并封顶。"""
    import random
    delay = min(base_delay * (2 ** attempt), max_delay)
    if jitter:
        delay *= 1 - jitter + 2 * jitter * random.random()
    return round(delay, 3)


def retry_call(func, args=(), kwargs=None, retries=3, base_delay=0.1,
               max_delay=2.0, should_retry=None, sleep=time.sleep):
    """调用 func,失败后按指数退避重试;最终失败抛出最后一次异常。"""
    kwargs = dict(kwargs or {})
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt >= retries:
                break
            if should_retry is not None and not should_retry(exc):
                break
            delay = compute_backoff(attempt, base_delay, max_delay)
            print(f"  第 {attempt + 1} 次调用失败:{type(exc).__name__}: {exc}")
            print(f"  等待 {delay:.2f}s 后重试")
            sleep(delay)
    raise last_exc


def main():
    print("== Agent 运行时底座 · s1:指数退避重试 ==")
    state = {"calls": 0}

    def flaky_service():
        state["calls"] += 1
        if state["calls"] < 3:
            raise TimeoutError("上游超时,请稍后重试")
        return f"ok(第 {state['calls']} 次成功)"

    result = retry_call(flaky_service, retries=3, base_delay=0.01,
                        max_delay=0.05, sleep=lambda _: None)
    print(f"  最终结果:{result}")

    def permanent_error():
        raise ValueError("参数不合法,重试也白搭")

    try:
        retry_call(permanent_error, should_retry=lambda e: isinstance(e, TimeoutError),
                   sleep=lambda _: None)
    except ValueError as exc:
        print(f"  不可重试异常直接抛出:ValueError: {exc}")

    print(f"  退避曲线(秒):{[compute_backoff(i) for i in range(5)]}")


if __name__ == "__main__":
    main()
