"""黑糖资料室 · t22-s2:MMR 去冗余 —— 纯相似度 vs 最大边际相关性对比。"""
import hashlib
import math
from dataclasses import dataclass

EMBED_DIM = 512

RAW_DOCS = [
    ("d01", "文档切分指南·基础", "文档切分需按标题、段落与长度边界处理,并保留必要的上下文重叠。", "切分,段落,上下文", 3),
    ("d02", "文档切分指南·进阶", "进阶切分需要保存来源元数据,并用重叠窗口避免语义在边界处丢失。", "切分,上下文", 40),
    ("d03", "查询改写方法", "查询改写应保留原始意图,补充同义表达后再进入召回阶段。", "查询,改写,召回", 5),
    ("d04", "错误恢复指南", "错误恢复应记录失败原因,再按重试、降级与状态恢复顺序处理。", "错误,恢复,稳定", 120),
    ("d05", "缓存失效策略", "缓存应绑定数据版本与有效期,源文档更新后必须及时失效。", "缓存,失效,版本", 200),
    ("d06", "服务恢复手册", "服务恢复手册记录重试、降级与状态恢复方法,用于处理常见运行异常。", "故障,恢复,重试", 10),
    ("d07", "引用校验清单", "引用校验需要核对来源编号、原文片段与回答事实是否一致。", "引用,校验,来源", 60),
    ("d08", "基础创作方法图解", "创作方法入门图解,刺撩劈扫四式,配图三十幅,适合初学。", "创作方法,入门", 2),
]


@dataclass
class Document:
    doc_id: str
    title: str
    text: str
    keywords: list
    updated_days_ago: int


def make_docs() -> list:
    return [Document(i, t, x, k.split(","), d) for i, t, x, k, d in RAW_DOCS]


def tokenize(text: str) -> list:
    chars = [c for c in text if not c.isspace()]
    return chars + ["".join(chars[i:i + 2]) for i in range(len(chars) - 1)]


def embed(text: str) -> list:
    vec = [0.0] * EMBED_DIM
    for tok in tokenize(text):
        digest = hashlib.md5(tok.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % EMBED_DIM
        vec[idx] += 1.0 if digest[4] % 2 == 0 else -1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list, b: list) -> float:
    return sum(x * y for x, y in zip(a, b))


class VectorStore:
    def __init__(self, docs: list):
        self.items = [(d, embed(d.title + "。" + d.text)) for d in docs]

    def search(self, query: str, k: int = 3) -> list:
        qv = embed(query)
        scored = [(d, cosine(qv, v)) for d, v in self.items]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


def mmr_search(store: VectorStore, query: str, k: int = 3, lambda_param: float = 0.5) -> list:
    """最大边际相关性:每轮贪心地选 lambda*相关性 - (1-lambda)*冗余度 最大的文档。

    冗余度 = 候选与已选集里任何一篇的最大余弦相似度。
    lambda 越靠近 1 越像纯相似度,越靠近 0 越追求多样。
    """
    qv = embed(query)
    pool = [(d, v, cosine(qv, v)) for d, v in store.items]
    selected = []
    while pool and len(selected) < k:
        def mmr_score(item):
            _, v, rel = item
            redundancy = max((cosine(v, sv) for _, sv, _ in selected), default=0.0)
            return lambda_param * rel - (1 - lambda_param) * redundancy
        best = max(pool, key=mmr_score)
        selected.append(best)
        pool = [c for c in pool if c[0].doc_id != best[0].doc_id]
    return [(d, rel) for d, _, rel in selected]


def avg_pairwise_sim(results: list) -> float:
    """结果集内部平均两两相似度:越低说明覆盖的角度越多样。"""
    vecs = [embed(d.title + "。" + d.text) for d, _ in results]
    pairs = [cosine(a, b) for i, a in enumerate(vecs) for b in vecs[i + 1:]]
    return sum(pairs) / len(pairs) if pairs else 0.0


def show(tag: str, results: list) -> None:
    print(f"=== {tag} ===")
    for rank, (doc, score) in enumerate(results, 1):
        print(f"TOP{rank} {doc.title} score={score:.4f}")
    print(f"内部平均相似度={avg_pairwise_sim(results):.4f}")


def main() -> None:
    store = VectorStore(make_docs())
    query = "文档切分应该怎么做"
    print(f"[查询] {query}")
    show("纯相似度 TOP3", store.search(query, k=3))
    show("MMR(lambda=0.5) TOP3", mmr_search(store, query, k=3, lambda_param=0.5))


if __name__ == "__main__":
    main()
