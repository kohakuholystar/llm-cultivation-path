"""黑糖资料室 · 第 7 步：真实 BGE 嵌入、元数据过滤与可重复行为测试。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


MODEL_NAME = "BAAI/bge-small-zh-v1.5"


class Embedder(Protocol):
    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...


class BgeEmbedder:
    """生产实现：仅加载本机缓存的 BAAI/bge-small-zh-v1.5。"""

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name, local_files_only=True)
        except ImportError as exc:
            raise RuntimeError("请先在本机执行: pip install sentence-transformers") from exc
        except OSError as exc:
            raise RuntimeError(
                f"本地未找到模型 {model_name}。请在受信任的联网开发机预下载并缓存后重试。"
            ) from exc

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self.model.encode(list(texts), normalize_embeddings=True)
        return vectors.tolist()


@dataclass(frozen=True)
class Passage:
    id: str
    text: str
    source: str
    category: str


def dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


class InMemoryVectorStore:
    """小语料参考实现；生产中可等价替换为 Chroma collection.query(where=...)。"""

    def __init__(self, embedder: Embedder) -> None:
        self.embedder = embedder
        self.passages: list[Passage] = []
        self.vectors: list[list[float]] = []

    def add(self, passages: Sequence[Passage]) -> None:
        self.passages = list(passages)
        self.vectors = self.embedder.encode([p.text for p in passages])

    def search(self, question: str, *, top_k: int = 3, category: str | None = None) -> list[dict]:
        query = self.embedder.encode([question])[0]
        candidates = [
            {"id": passage.id, "text": passage.text, "source": passage.source,
             "category": passage.category, "score": dot(query, vector)}
            for passage, vector in zip(self.passages, self.vectors)
            if category is None or passage.category == category
        ]
        return sorted(candidates, key=lambda item: item["score"], reverse=True)[:top_k]


def answer_question(store: InMemoryVectorStore, question: str, *, min_score: float = 0.55) -> dict:
    hits = store.search(question, top_k=3)
    if not hits or hits[0]["score"] < min_score:
        return {"answer": "根据现有资料无法回答。", "citations": []}
    best = hits[0]
    return {
        "answer": f"根据资料：{best['text']}",
        "citations": [best["source"]],
    }
