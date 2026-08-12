from app.agent import DujieAgent
from app.schemas import Answer, RetrievalHit, RetrievalQuery


class StubKnowledgeBase:
    """只替换 t71 的实现，不替换 t72 对公开接口的依赖。"""

    def ask(self, query: RetrievalQuery) -> Answer:
        return Answer(
            text=f"关于 {query.question} 的可验证回答",
            sources=[
                RetrievalHit(
                    document_id="manual-1",
                    title="部署手册",
                    content="健康检查使用 /healthz。",
                    score=1.0,
                )
            ],
        )


def test_agent_delegates_to_rag_contract_and_preserves_citations() -> None:
    answer = DujieAgent(StubKnowledgeBase()).answer("如何检查服务")
    assert "如何检查服务" in answer.text
    assert [source.title for source in answer.sources] == ["部署手册"]
