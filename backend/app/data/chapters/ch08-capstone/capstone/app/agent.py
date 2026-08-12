"""t72 实现 Agent。它必须直接导入 t71 的 KnowledgeBase 接口。"""
from app.rag import KnowledgeBase
from app.schemas import Answer, RetrievalQuery


class DujieAgent:
    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self.knowledge_base = knowledge_base

    def answer(self, question: str) -> Answer:
        return self.knowledge_base.ask(RetrievalQuery(question=question))
