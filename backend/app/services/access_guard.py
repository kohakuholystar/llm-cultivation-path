"""公网访问防护(服务器版): 访问口令 + 按 IP 限流 + 沙箱运行日志。

设计原则:
- 口令为空 = 关闭门槛, 本地开发完全无感; 配了 ACCESS_CODES 才启用
- 限流是每 IP 每分钟滑动窗口, 内存实现无需外部依赖; 0 = 不限
- 运行日志写 backend/logs/sandbox.log: 谁、何时、跑了多大的代码、结果如何
  (运营者就是一个人, tail 日志比监控后台实在)
"""
from __future__ import annotations

import logging
import time
from collections import deque

from fastapi import HTTPException, Request

from app.config import settings
from app.models.sandbox import SandboxRunRequest, SandboxRunResponse

_logger = logging.getLogger("sandbox.guard")


def _ensure_log_handler() -> None:
    """懒挂 FileHandler(避免 import 副作用; 重复调用安全)。"""
    if _logger.handlers:
        return
    log_dir = settings.backend_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_dir / "sandbox.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


def client_ip(request: Request) -> str:
    """优先取反向代理透传的真实 IP(X-Forwarded-For 首个)。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_access(request: Request) -> None:
    """访问口令: 未配置 ACCESS_CODES 时全部放行。"""
    codes = settings.access_codes_list
    if not codes:
        return
    if request.headers.get("x-access-code", "") not in codes:
        _ensure_log_handler()
        _logger.warning(f"拒绝访问 ip={client_ip(request)} (口令错误/缺失)")
        raise HTTPException(
            403, "访问口令错误或缺失:服务器版需要邀请码,请在右上角 AI 配置中填入"
        )


# 滑动窗口: ip -> 最近 60 秒内的请求时间戳
_buckets: dict[str, deque[float]] = {}


def check_rate_limit(request: Request) -> None:
    """按 IP 限流: SANDBOX_RATE_LIMIT 次/分钟, 0 = 不限。"""
    limit = settings.sandbox_rate_limit
    if limit <= 0:
        return
    ip = client_ip(request)
    now = time.monotonic()
    bucket = _buckets.setdefault(ip, deque())
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    if len(bucket) >= limit:
        _ensure_log_handler()
        _logger.warning(f"限流 ip={ip} ({len(bucket)}/{limit})")
        raise HTTPException(429, f"请求太频繁:每 IP 每分钟限 {limit} 次沙箱运行,请稍后再试")
    bucket.append(now)


def log_run(request: Request, req: SandboxRunRequest, resp: SandboxRunResponse) -> None:
    """每次沙箱运行留痕(口令本身不落日志, 只记是否携带)。"""
    _ensure_log_handler()
    has_code = "yes" if request.headers.get("x-access-code") else "no"
    _logger.info(
        f"run ip={client_ip(request)} invite={has_code} "
        f"size={len(req.code)}B net={req.needs_network} "
        f"exit={resp.exit_code} timed_out={resp.timed_out} {resp.duration_ms}ms"
    )
