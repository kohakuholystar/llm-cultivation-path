"""终期交付 · s3:docker-compose 编排
从「一个镜像」升级到「一套服务」:用 compose 把服务编排起来——
构建、端口、密钥注入、健康检查一条龙。文本先写后审,yaml 解析把关。
"""


# === 学习契约（面向学生）===
# 本节目标：docker-compose 编排:一键拉起。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `write_service(path: str) -> str`：输入为签名中的参数；输出为 `str`。用途：把服务源码写到磁盘,返回路径。
#   - `audit_compose(text: str) -> list[str]`：输入为签名中的参数；输出为 `list[str]`。用途：解析 compose 文本,校验服务、端口、环境与健康检查,返回问题清单。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import yaml

# 目标服务源码(s1 产物,原样复用)
SERVICE_PY = """# 黑糖资料室 · Agent 应用 HTTP 服务(由构建脚本生成)。
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="黑糖资料室", version="0.1.0")

@app.get("/health")
def health() -> dict:
    # 存活探针:进程在,服务在。
    return {"status": "ok", "service": "dujie-feisheng",
            "model": os.getenv("MODEL_NAME", "deepseek-v4-pro")}

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

@app.post("/api/chat")
def chat(req: ChatRequest) -> dict:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    return {"session_id": req.session_id, "reply": f"[演示] 收到:{req.message[:20]}"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
"""


def write_service(path: str) -> str:
    """把服务源码写到磁盘,返回路径。"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(SERVICE_PY)
    return path


# 镜像说明书(s2 产物,原样复用)
DOCKERFILE = """# 黑糖资料室 · 服务镜像(由 s2 生成)。
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# 编排文件 docker-compose.yml(由 s3 生成)。密钥经环境变量注入,不进镜像。
COMPOSE = """# 黑糖资料室 · 编排(由 s3 生成)。
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
    # TODO: 依次检查 app 的 build、端口映射、密钥注入与 healthcheck,缺项追加进 problems
    # 提示: "build" 不在 app        -> "app 缺少 build 指令,镜像从哪来?";
    #       app.get("ports") != ["8000:8000"] -> "端口映射应为 8000:8000";
    #       "DEEPSEEK_API_KEY" 不在 (app.get("environment") or {}) -> "environment 缺少 DEEPSEEK_API_KEY 注入";
    #       "healthcheck" 不在 app  -> "app 缺少 healthcheck,容器挂了自己都不知道"
    raise NotImplementedError("t73-docker-deploy-s3 尚未实现:请按 TODO 提示完成 compose 四项校验")
    return problems


def main() -> None:
    write_service("main.py")
    with open("Dockerfile", "w", encoding="utf-8") as f:
        f.write(DOCKERFILE)
    with open("docker-compose.yml", "w", encoding="utf-8") as f:
        f.write(COMPOSE)
    print("== 交付物 ==")
    print("  main.py / Dockerfile / docker-compose.yml 已就位")
    print("== compose 审计 ==")
    problems = audit_compose(COMPOSE)
    if problems:
        for p in problems:
            print(f"  [x] {p}")
        print("  compose 有缺漏,先补齐再谈编排。")
    else:
        print("  全部合格:服务、端口、密钥注入、健康检查一应俱全。")
        print("  一键拉起:docker compose up -d --build")


if __name__ == "__main__":
    main()
