"""Trusted behaviour tests for t21-s7.

The production implementation is BgeEmbedder.  These tests deliberately use a
deterministic test double: model weights are not downloaded in a sandbox, while
the retrieval, metadata, refusal, citation, and Recall@k contracts are tested.
"""
from student_submission import InMemoryVectorStore, Passage, answer_question


class DeterministicEmbedder:
    vectors = {
        "基础指南数据清洗": [1.0, 0.0, 0.0],
        "创作方法要诀": [0.0, 1.0, 0.0],
        "止血药方": [0.0, 0.0, 1.0],
        "如何练基础指南": [1.0, 0.0, 0.0],
        "创作方法": [0.0, 1.0, 0.0],
        "受伤止血": [0.0, 0.0, 1.0],
        "意大利面": [0.0, 0.0, 0.0],
    }

    def encode(self, texts):
        return [self.vectors[text] for text in texts]


PASSAGES = [
    Passage("d1", "基础指南数据清洗", "基础指南总纲.pdf#p1", "基础指南"),
    Passage("d2", "创作方法要诀", "输出模板.pdf#p2", "创作方法"),
    Passage("d3", "止血药方", "药典.pdf#p8", "医药"),
]


def make_store():
    store = InMemoryVectorStore(DeterministicEmbedder())
    store.add(PASSAGES)
    return store


def recall_at_k(question, relevant_id, k=1):
    return int(any(hit["id"] == relevant_id for hit in make_store().search(question, top_k=k)))


def test_recall_at_one_is_repeatable_for_three_known_questions():
    cases = [("如何练基础指南", "d1"), ("创作方法", "d2"), ("受伤止血", "d3")]
    assert sum(recall_at_k(question, expected) for question, expected in cases) / len(cases) == 1.0


def test_metadata_filter_is_pre_filter_not_display_only():
    hits = make_store().search("如何练基础指南", top_k=3, category="创作方法")
    assert [hit["id"] for hit in hits] == ["d2"]
    assert all(hit["category"] == "创作方法" for hit in hits)


def test_out_of_corpus_question_refuses_to_answer():
    assert answer_question(make_store(), "意大利面") == {
        "answer": "根据现有资料无法回答。", "citations": []
    }


def test_citation_is_from_the_retrieved_passage():
    result = answer_question(make_store(), "受伤止血")
    assert result["citations"] == ["药典.pdf#p8"]
    assert "止血药方" in result["answer"]
