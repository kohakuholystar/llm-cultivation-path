"""t70 的可运行 API 骨架；t73 在此基础上增加业务路由与部署配置。"""
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="黑糖资料室", version="0.1.0")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
