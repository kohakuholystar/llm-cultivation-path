"""终期交付 · s1:FastAPI 服务封装
把前几关打磨好的 Agent 应用封装为 HTTP 服务:先写出 main.py 的完整源码,
再用 ast 做「源码审计」——不依赖 fastapi 也能解析结构、盘点路由。
"""


# === 学习契约（面向学生）===
# 本节目标：FastAPI 服务封装:源码审计先行。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `write_service(path: str) -> str`：输入为签名中的参数；输出为 `str`。用途：把服务源码写到磁盘,返回路径。
#   - `audit_service(source: str) -> list[dict]`：输入为签名中的参数；输出为 `list[dict]`。用途：用 ast 解析服务源码,盘点每条路由:方法、路径、处理函数。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import ast

# 目标服务 main.py 的完整源码(文本)。真实项目里,这一步就是把文件真实写出。
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


def audit_service(source: str) -> list[dict]:
    """用 ast 解析服务源码,盘点每条路由:方法、路径、处理函数。"""
    tree = ast.parse(source)
    routes = []
    # TODO: 遍历 tree 的全部节点,对函数节点逐一处理装饰器,盘点出全部路由
    # 提示: ast.walk(tree) 里只取 ast.FunctionDef / ast.AsyncFunctionDef;装饰器须是
    #       ast.Call 且 func 是 ast.Attribute(形如 app.get),method 取 dec.func.attr,
    #       path 取 dec.args[0].value(无参兜底 "?");method 以 get/post/put/delete 开头
    #       才计入,把 {"method": method.upper(), "path": path, "func": node.name} 追加进 routes
    raise NotImplementedError("t73-docker-deploy-s1 尚未实现:请按 TODO 提示遍历 AST 盘点路由")
    return routes


def main() -> None:
    path = write_service("main.py")
    routes = audit_service(SERVICE_PY)
    print(f"== 服务源码审计 {path} ==")
    print(f"  源码 {len(SERVICE_PY.splitlines())} 行,AST 顶层节点 {len(ast.parse(SERVICE_PY).body)} 个")
    for r in routes:
        print(f"  {r['method']:<6} {r['path']:<12} -> {r['func']}")
    if routes:
        print(f"  共发现 {len(routes)} 条路由,结构合格,可以进入镜像封装。")
    else:
        print("  [警告] 一条路由都没有,这样的服务上线等于没上线!")


if __name__ == "__main__":
    main()
