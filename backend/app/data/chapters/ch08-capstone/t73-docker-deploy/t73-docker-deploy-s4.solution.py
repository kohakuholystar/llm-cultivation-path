"""渡劫飞升 · s4:健康检查与就绪判定
compose 里的 healthcheck 是容器级探针,本步实现应用级探针:
读取服务上报的状态快照,按存活(liveness)与就绪(readiness)两组规则
逐项判定,把 /health 从「进程还活着」升级为「能干活」。
"""
import yaml

# 编排文件(s3 产物,原样复用;其中的 healthcheck 就是容器级探针)
COMPOSE = """# 渡劫飞升 · 编排(由 s3 生成)。
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DEEPSEEK_API_KEY: "${DEEPSEEK_API_KEY:?请在 .env 中配置}"
      MODEL_NAME: deepseek-v4-pro
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
"""


def audit_compose(text: str) -> list[str]:
    """解析 compose 文本,校验服务、端口、环境与健康检查,返回问题清单。"""
    problems = []
    try:
        data = yaml.safe_load(text) or {}
    except Exception as exc:
        return [f"compose 无法解析: {exc}"]
    services = data.get("services") or {}
    if not services:
        problems.append("services 为空,至少要有 app 服务")
    app = services.get("app") or {}
    if "build" not in app:
        problems.append("app 缺少 build 指令,镜像从哪来?")
    if app.get("ports") != ["8000:8000"]:
        problems.append("端口映射应为 8000:8000")
    env = app.get("environment") or {}
    if "DEEPSEEK_API_KEY" not in env:
        problems.append("environment 缺少 DEEPSEEK_API_KEY 注入")
    if "healthcheck" not in app:
        problems.append("app 缺少 healthcheck,容器挂了自己都不知道")
    return problems


# 服务状态快照:真实项目里由 /health 接口返回,这里用固定样例模拟
STATUS_SAMPLE = {
    "status": "ok",
    "service": "dujie-feisheng",
    "uptime_sec": 42,
    "deps": {"rag_index": "ready", "embedding": "ready", "llm": "unreachable"},
}

# 存活规则:进程活着就通过;就绪规则:依赖就绪才接流量
LIVENESS_RULES = [
    ("服务存活", lambda s: s.get("status") == "ok", "status 字段必须为 ok"),
    ("进程存活", lambda s: s.get("uptime_sec", 0) >= 0, "uptime_sec 必须非负"),
]

READINESS_RULES = [
    ("RAG 索引就绪", lambda s: s["deps"].get("rag_index") == "ready", "rag_index 未就绪"),
    ("Embedding 就绪", lambda s: s["deps"].get("embedding") == "ready", "embedding 未就绪"),
    ("LLM 可连通", lambda s: s["deps"].get("llm") == "ready", "llm 未就绪时功能受限,仍可启动"),
]


def check_health(status: dict) -> tuple[bool, list[dict]]:
    """按两组规则逐项判定,返回 (整体是否健康, 明细)。"""
    details = []
    for name, rule, reason in LIVENESS_RULES + READINESS_RULES:
        ok = bool(rule(status))
        details.append({"check": name, "ok": ok, "reason": reason})
    return all(d["ok"] for d in details), details


def summarize(ok: bool, details: list[dict]) -> None:
    """打印探针明细与最终裁决。"""
    for d in details:
        mark = "通过" if d["ok"] else "未通过"
        print(f"  [{mark}] {d['check']}:{d['reason']}")
    if ok:
        print("  整体就绪:返回 HTTP 200,流量放行。")
    else:
        print("  未就绪:返回 HTTP 503,负载均衡不应分发流量。")


def main() -> None:
    print("== 容器级探针:compose 中的 healthcheck ==")
    problems = audit_compose(COMPOSE)
    print("  全部合格" if not problems else "  " + " ".join(problems))
    print("== 应用级探针:基于状态快照 ==")
    ok, details = check_health(STATUS_SAMPLE)
    summarize(ok, details)
    print("[总结] 进程活着只是及格线,依赖就绪才算优秀;liveness 与 readiness 缺一不可。")


if __name__ == "__main__":
    main()
