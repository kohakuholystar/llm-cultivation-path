"""终期交付 · s2:Dockerfile 编写
把 s1 的服务源码装进标准 Docker 镜像:写出 Dockerfile 文本,再逐行审计
必备指令,确保这份「镜像说明书」在 docker build 时不会缺胳膊少腿。
"""


# === 学习契约（面向学生）===
# 本节目标：Dockerfile 编写:镜像说明书。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `write_service(path: str) -> str`：输入为签名中的参数；输出为 `str`。用途：把服务源码写到磁盘,返回路径。
#   - `audit_dockerfile(text: str) -> list[str]`：输入为签名中的参数；输出为 `list[str]`。用途：逐行解析 Dockerfile,检查必备指令,返回缺失清单。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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


# 镜像说明书 Dockerfile(由 s2 生成)。指令顺序决定镜像层缓存命中率。
DOCKERFILE = """# 黑糖资料室 · 服务镜像(由 s2 生成)。
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

REQUIRED_DIRECTIVES = {
    "FROM": "基础镜像,一切文件的起点",
    "WORKDIR": "工作目录,让 COPY 与 CMD 有明确落点",
    "COPY": "把依赖清单与代码送进镜像",
    "RUN": "在镜像内执行命令(如安装依赖)",
    "EXPOSE": "声明容器对外端口",
    "CMD": "容器启动时的默认命令",
}


def audit_dockerfile(text: str) -> list[str]:
    """逐行解析 Dockerfile,检查必备指令,返回缺失清单。"""
    problems = []
    lines = [ln.strip() for ln in text.splitlines()
             if ln.strip() and not ln.strip().startswith("#")]
    if not lines or not lines[0].startswith("FROM"):
        problems.append("Dockerfile 必须以 FROM 基础镜像指令开头")
    # TODO: 逐项核对 REQUIRED_DIRECTIVES,把缺失的必备指令追加进 problems
    # 提示: for directive, why in REQUIRED_DIRECTIVES.items():
    #       if not any(ln.startswith(directive) for ln in lines):
    #           problems.append(f"缺少 {directive} 指令({why})")
    raise NotImplementedError("t73-docker-deploy-s2 尚未实现:请按 TODO 提示核对 Dockerfile 必备指令")
    return problems


def main() -> None:
    service = write_service("main.py")
    with open("Dockerfile", "w", encoding="utf-8") as f:
        f.write(DOCKERFILE)
    print("== 交付物 ==")
    print(f"  {service}({len(SERVICE_PY.splitlines())} 行)")
    print(f"  Dockerfile({len(DOCKERFILE.splitlines())} 行)")
    print("== Dockerfile 审计 ==")
    problems = audit_dockerfile(DOCKERFILE)
    if problems:
        for p in problems:
            print(f"  [x] {p}")
        print("  Dockerfile 有缺漏,先补齐再谈构建。")
    else:
        print("  全部合格:基础镜像、工作目录、依赖、端口、启动命令齐备。")
        print("  体积贴士:依赖清单先行 COPY,代码后 COPY,可吃满镜像层缓存。")


if __name__ == "__main__":
    main()
