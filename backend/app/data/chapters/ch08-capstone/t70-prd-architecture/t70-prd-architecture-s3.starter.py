"""渡劫飞升 · s3:数据模型——Pydantic 契约先行

先定义数据契约,再写业务逻辑:文档、切块、典籍库、检索请求、
检索命中五份模型,把「知识库里存什么、请求长什么样」一次说清。
"""
import json
import os

from pydantic import BaseModel, Field, ValidationError


class Document(BaseModel):
    """一篇典籍原文:入库的最小单元。"""

    doc_id: str = Field(description="唯一文档 ID,如 kb-0001")
    title: str = Field(description="典籍标题,如《筑基入门》")
    author: str = Field(default="佚名", description="作者或出处")
    text: str = Field(description="典籍正文")
    tags: list[str] = Field(default_factory=list, description="分类标签")


class Chunk(BaseModel):
    """正文切块:检索的最小单元,命中时返回给上层。"""

    # TODO: 定义 4 个字段,全部用 Field 给出约束与中文说明
    # 提示: chunk_id、doc_id、content 三个 str 字段用 Field(description=...);
    #       order 是 int 且 Field(ge=0),块内序号从 0 开始
    raise NotImplementedError("t70-prd-architecture-s3 尚未实现:请按 TODO 提示补全 Chunk 字段")


class KnowledgeBase(BaseModel):
    """典籍库:文档与切块两棵树的根。"""

    docs: list[Document] = Field(default_factory=list)
    chunks: list[Chunk] = Field(default_factory=list)


class RetrievalQuery(BaseModel):
    """检索请求契约:文本 + 数量 + 门槛。"""

    # TODO: 定义 3 个字段,让非法请求在进业务前被拦下
    # 提示: text: str 用 Field(min_length=2, max_length=200);
    #       top_k: int 用 Field(gt=0, le=20);
    #       threshold: float 用 Field(ge=0.0, le=1.0, default=0.5)
    raise NotImplementedError("t70-prd-architecture-s3 尚未实现:请按 TODO 提示补全 RetrievalQuery 字段")


class RetrievalHit(BaseModel):
    """检索命中:一条结果,供回答组装引用。"""

    chunk_id: str
    score: float = Field(ge=0.0, le=1.0)
    snippet: str = Field(description="命中文本节选")


def build_sample_kb() -> KnowledgeBase:
    """造一份样例库,演示契约如何落地。"""
    doc = Document(doc_id="kb-0001", title="《筑基入门》", text="引气入体,守心如一。")
    return KnowledgeBase(
        docs=[doc],
        chunks=[Chunk(chunk_id="kb-0001-0", doc_id="kb-0001", content="引气入体,守心如一。", order=0)],
    )


def demo_schemas() -> None:
    """把四份契约导出成 JSON Schema,落盘供前端复用。"""
    models = {
        "Document": Document.model_json_schema(),
        "Chunk": Chunk.model_json_schema(),
        "RetrievalQuery": RetrievalQuery.model_json_schema(),
        "RetrievalHit": RetrievalHit.model_json_schema(),
    }
    os.makedirs("docs", exist_ok=True)
    with open("docs/data_models.json", "w", encoding="utf-8") as f:
        json.dump(models, f, ensure_ascii=False, indent=2)
    print(f"已写入 docs/data_models.json,共 {len(models)} 个契约")


def demo_validation() -> None:
    """演示非法请求被契约拦下:top_k=0 越界。"""
    try:
        RetrievalQuery(text="如何筑基", top_k=0)
    except ValidationError as exc:
        err = exc.errors()[0]
        print(f"拦截成功:字段 {err['loc'][0]} 违规:{err['msg']}")


def main() -> None:
    kb = build_sample_kb()
    print(f"样例库载入 {len(kb.docs)} 篇文档、{len(kb.chunks)} 个切块")
    demo_schemas()
    demo_validation()


if __name__ == "__main__":
    main()
