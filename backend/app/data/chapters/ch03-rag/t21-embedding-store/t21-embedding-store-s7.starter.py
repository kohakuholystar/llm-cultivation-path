"""黑糖资料室 · 第 7 步：使用本地 BGE 模型，并用行为测试守住检索契约。

准备（只在自己的开发机执行一次，不在课程沙箱中下载模型）：
    pip install sentence-transformers
    # 连网时首次运行会缓存 BAAI/bge-small-zh-v1.5；之后本文件只读本地缓存。
"""
# 学习契约
# 目标：完成 t21-embedding-store-s7 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 6 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：answer_question(store, question, *min_score) -> dict。
# 技术栈：__future__, dataclasses, typing。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


MODEL_NAME = "BAAI/bge-small-zh-v1.5"


class Embedder(Protocol):
    """向量库依赖的最小接口；BgeEmbedder 是生产实现，测试可传入测试替身。"""

    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...


class BgeEmbedder:
    """只加载已经缓存的真实 BGE 中文模型，绝不在运行时隐式下载。"""

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
        # TODO: 调用真实模型，要求归一化，并转成普通 list 交给向量库。
        raise NotImplementedError("请实现 BgeEmbedder.encode")


@dataclass(frozen=True)
class Passage:
    id: str
    text: str
    source: str
    category: str


class InMemoryVectorStore:
    """小语料的可测向量库：真实项目可把它替换为 Chroma，而不改变 search 契约。"""

    def __init__(self, embedder: Embedder) -> None:
        self.embedder = embedder
        self.passages: list[Passage] = []
        self.vectors: list[list[float]] = []

    def add(self, passages: Sequence[Passage]) -> None:
        self.passages = list(passages)
        self.vectors = self.embedder.encode([p.text for p in passages])

    def search(self, question: str, *, top_k: int = 3, category: str | None = None) -> list[dict]:
        # TODO: 编码问题；仅在指定 category 的候选中按点积降序取 top_k。
        # 返回每项必须含 id/text/source/category/score，供回答层引用与拒答判断。
        raise NotImplementedError("请实现带 metadata filter 的 search")


def answer_question(store: InMemoryVectorStore, question: str, *, min_score: float = 0.55) -> dict:
    """检索为空或最高分不足时明确拒答；否则返回可追溯引用，而非让模型猜测。"""
    # TODO: 调用 search；低置信度返回 {"answer": "根据现有资料无法回答。", "citations": []}。
    # 命中时返回 citations 中的 source，且每条 citation 必须来自实际命中 passage。
    raise NotImplementedError("请实现无答案拒答与引用")
