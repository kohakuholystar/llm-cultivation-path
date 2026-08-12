"""终期交付 · s6:收官部署,一键上线
把前五步的产物收拢成一个部署包:四份文件一次写齐,体检、探针、上线报告
一气呵成——这就是「终期交付」毕业设计的交付形态。
"""
import os
import sys
import yaml
from dataclasses import dataclass

MOCK = os.environ.get("MOCK_LLM") == "1"          # 演示模式:无网时走剧本
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("请先在右上角 AI 配置填入 DeepSeek API Key")
    sys.exit(0)

# 生产版服务源码(s1 产物的精简复刻)
SERVICE_PY = """# 黑糖资料室 · Agent 应用 HTTP 服务(生产版)。
from fastapi import FastAPI

app = FastAPI(title="黑糖资料室", version="0.1.0")

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "dujie-feisheng"}

@app.post("/api/chat")
def chat(req: dict) -> dict:
    return {"reply": f"[演示] 收到:{str(req.get('message', ''))[:20]}"}
"""

# 镜像说明书(s2 产物)
DOCKERFILE = """# 黑糖资料室 · 服务镜像(由 s2 生成)。
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# 编排文件(s3 产物)
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

# 环境样例(s5 产物)
ENV_EXAMPLE = """# 黑糖资料室 · 环境配置样例(由 s5 生成)。
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
MODEL_NAME=deepseek-v4-pro
"""


@dataclass
class Config:
    host: str = "0.0.0.0"
    port: int = 8000
    model_name: str = "deepseek-v4-pro"
    api_key: str = ""

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", "8000")),
            model_name=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
            api_key=os.environ.get("OPENAI_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", ""),
        )


# 毕业状态快照:一切依赖就绪
STATUS_SAMPLE = {"status": "ok", "uptime_sec": 42,
                 "deps": {"rag_index": "ready", "embedding": "ready", "llm": "ready"}}


def probe_health(status: dict) -> list[str]:
    """最小探针:存活 + 就绪,返回未通过的检查名列表。"""
    checks = [
        ("存活", status.get("status") == "ok"),
        ("RAG 索引", status["deps"].get("rag_index") == "ready"),
        ("Embedding", status["deps"].get("embedding") == "ready"),
        ("LLM", status["deps"].get("llm") == "ready"),
    ]
    return [name for name, ok in checks if not ok]


def check_artifacts(files: dict[str, str]) -> list[str]:
    """对部署包四份文件做最终体检,返回问题清单。"""
    problems = []
    service = files.get("main.py", "")
    if '@app.get("/health")' not in service:
        problems.append("main.py 缺少 /health 存活路由")
    if "@app.post" not in service:
        problems.append("main.py 缺少业务路由")
    for directive in ("FROM", "WORKDIR", "COPY", "CMD"):
        if not any(ln.strip().startswith(directive) for ln in files.get("Dockerfile", "").splitlines() if ln.strip()):
            problems.append(f"Dockerfile 缺少 {directive}")
    data = yaml.safe_load(files.get("docker-compose.yml", "")) or {}
    if "app" not in (data.get("services") or {}):
        problems.append("compose 缺少 app 服务")
    if "healthcheck" not in (data.get("services") or {}).get("app", {}):
        problems.append("compose 缺少 healthcheck")
    if ".env.example" not in files:
        problems.append("缺少 .env.example 模板")
    return problems


def main() -> None:
    cfg = Config.from_env()
    files = {
        "main.py": SERVICE_PY,
        "Dockerfile": DOCKERFILE,
        "docker-compose.yml": COMPOSE,
        ".env.example": ENV_EXAMPLE,
    }
    for name, text in files.items():
        with open(name, "w", encoding="utf-8") as f:
            f.write(text)
    problems = check_artifacts(files)
    failed = probe_health(STATUS_SAMPLE)
    print("== 黑糖资料室 · 上线报告 ==")
    print(f"  服务: {cfg.host}:{cfg.port}  模型: {cfg.model_name}")
    print(f"  部署包: {', '.join(files)}")
    if problems or failed:
        for p in problems:
            print(f"  [x] {p}")
        for name in failed:
            print(f"  [x] 探针未通过: {name}")
        print("  结论:暂不满足上线条件,修复后重新自检。")
    else:
        print("  代码审计: 通过")
        print("  健康探针: 通过")
        print("  结论:满足上线条件,交付运维。黑糖资料室,圆满收官!")


if __name__ == "__main__":
    main()
