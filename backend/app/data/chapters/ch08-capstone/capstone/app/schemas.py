"""t70 固定的数据与 HTTP 契约；t71/t72 直接导入，不重复定义。"""
from pydantic import BaseModel, Field


class DocumentIn(BaseModel):
    document_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)


class RetrievalQuery(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)


class RetrievalHit(BaseModel):
    document_id: str
    title: str
    content: str
    score: float = Field(ge=0, le=1)


class Answer(BaseModel):
    text: str
    sources: list[RetrievalHit]
