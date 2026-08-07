"""渡劫飞升 · s4:接口契约——OpenAPI 3.0 规格生成

把 s3 的 Pydantic 模型提升为对外 API:用 EndpointSpec 声明四个
接口的入参出参,再由 build_openapi 组装成 OpenAPI 3.0 规格,
落盘为 YAML,前后端按同一份文档联调。
"""
import os
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field


class Document(BaseModel):
    """一篇典籍原文(浓缩自 s3)。"""

    doc_id: str = Field(description="唯一文档 ID")
    title: str = Field(description="典籍标题")
    text: str = Field(description="典籍正文")


class RetrievalQuery(BaseModel):
    """检索请求(浓缩自 s3)。"""

    text: str = Field(min_length=2, description="用户提问")
    top_k: int = Field(default=5, gt=0, le=20, description="返回条数")


class RetrievalHit(BaseModel):
    """检索命中(浓缩自 s3)。"""

    chunk_id: str
    score: float = Field(ge=0.0, le=1.0)


class EndpointSpec(BaseModel):
    """一个接口的契约:方法、路径、摘要、请求体、响应体。"""

    method: Literal["GET", "POST"]
    path: str
    summary: str
    request_schema: Optional[dict] = Field(default=None, description="请求体 JSON Schema")
    response_schema: dict = Field(description="响应体 JSON Schema")


def endpoints() -> list:
    """四个核心接口:建库、入库、检索、健康检查。"""
    # TODO: 补全 4 个 EndpointSpec,请求体 Schema 用 model_json_schema() 生成
    # 提示: POST /api/kb(Document)、POST /api/kb/documents(Document)、
    #       POST /api/retrieve(RetrievalQuery,响应含 hits)、
    #       GET /api/health(无请求体,request_schema=None);
    #       return [EndpointSpec(...), ...]
    raise NotImplementedError("t70-prd-architecture-s4 尚未实现:请按 TODO 提示补全 endpoints")


def build_openapi(specs: list) -> dict:
    """把接口清单组装成 OpenAPI 3.0 根文档。"""
    info = {"title": "渡劫飞升 · 知识问答 API", "version": "0.1.0"}
    paths = {}
    for ep in specs:
        body = None if ep.request_schema is None else {
            "required": True,
            "content": {"application/json": {"schema": ep.request_schema}},
        }
        paths.setdefault(ep.path, {})[ep.method.lower()] = {
            "summary": ep.summary,
            "requestBody": body,
            "responses": {
                "200": {
                    "description": "成功",
                    "content": {"application/json": {"schema": ep.response_schema}},
                }
            },
        }
    return {"openapi": "3.0.3", "info": info, "paths": paths}


def render_yaml(doc: dict) -> str:
    """导出 YAML,保留中文与字段顺序。"""
    return yaml.dump(doc, allow_unicode=True, sort_keys=False)


def verify_contract(text: str) -> None:
    """读回生成的 YAML,校验路径与接口数量。"""
    # TODO: 读回 YAML,统计路径与方法数量并逐一断言
    # 提示: loaded = yaml.safe_load(text);paths = loaded["paths"];
    #       n_paths = len(paths);n_ops = sum(len(ops) for ops in paths.values());
    #       断言 n_paths == 4、n_ops == 4、"/api/retrieve" in paths;
    #       打印 f"契约校验通过:{n_paths} 条路径、{n_ops} 个方法,含 /api/retrieve"
    raise NotImplementedError("t70-prd-architecture-s4 尚未实现:请按 TODO 提示补全 verify_contract")


def main() -> None:
    os.makedirs("docs", exist_ok=True)
    text = render_yaml(build_openapi(endpoints()))
    with open("docs/openapi.yaml", "w", encoding="utf-8") as f:
        f.write(text)
    verify_contract(text)
    print(f"已写入 docs/openapi.yaml,共 {len(endpoints())} 个接口")


if __name__ == "__main__":
    main()
