"""t71 实现 RAG；t72 的 Agent 只依赖这个公开边界。"""
from typing import Protocol

from app.schemas import Answer, DocumentIn, RetrievalQuery


class KnowledgeBase(Protocol):
    def ingest(self, document: DocumentIn) -> None:
        """写入一篇文档；重复写入同一 document_id 必须幂等。"""

    def ask(self, query: RetrievalQuery) -> Answer:
        """返回回答及可追溯来源；无命中也必须返回空 sources。"""
