"""渡劫飞升 · s1:FastAPI 服务封装
把前几关打磨好的 Agent 应用封装为 HTTP 服务:先写出 main.py 的完整源码,
再用 ast 做「源码审计」——不依赖 fastapi 也能解析结构、盘点路由。
"""
import ast

# 目标服务 main.py 的完整源码(文本)。真实项目里,这一步就是把文件真实写出。
SERVICE_PY = """# 渡劫飞升 · Agent 应用 HTTP 服务(由构建脚本生成)。
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="渡劫飞升", version="0.1.0")

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
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
                continue
            method = dec.func.attr
            if not method.startswith(("get", "post", "put", "delete")):
                continue
            path = dec.args[0].value if dec.args else "?"
            routes.append({"method": method.upper(), "path": path, "func": node.name})
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
