"""黑糖资料室 · t22-s6:检索管线总装 —— 向量检索 -> MMR -> 阈值过滤 -> 重排序,并做三策略总评测。"""
import hashlib
import math
from dataclasses import dataclass

EMBED_DIM, SCORE_THRESHOLD = 512, 0.12

RAW_DOCS = [  # (编号, 标题, 正文, 主题词, 距今更新天数)
    ("d01", "文档切分指南·基础", "文档切分需按标题、段落与长度边界处理,并保留必要的上下文重叠。", "切分,段落,上下文", 3),
    ("d02", "文档切分指南·进阶", "进阶切分需要保存来源元数据,并用重叠窗口避免语义在边界处丢失。", "切分,上下文", 40),
    ("d03", "查询改写方法", "查询改写应保留原始意图,补充同义表达后再进入召回阶段。", "查询,改写,召回", 5),
    ("d04", "错误恢复指南", "错误恢复应记录失败原因,再按重试、降级与状态恢复顺序处理。", "错误,恢复,稳定", 120),
    ("d05", "缓存失效策略", "缓存应绑定数据版本与有效期,源文档更新后必须及时失效。", "缓存,失效,版本", 200),
    ("d06", "服务恢复手册", "服务恢复手册记录重试、降级与状态恢复方法,用于处理常见运行异常。", "故障,恢复,重试", 10),
    ("d07", "引用校验清单", "引用校验需要核对来源编号、原文片段与回答事实是否一致。", "引用,校验,来源", 60),
    ("d08", "基础创作方法图解", "创作方法入门图解,刺撩劈扫四式,配图三十幅,适合初学。", "创作方法,入门", 2),
]
EVAL_SET = [("如何按段落切分并保留上下文", "d01"), ("稳定的错误恢复方法", "d04"),  # 标注集
            ("服务故障后如何恢复", "d06"), ("引用结果如何校验", "d07"), ("初学者怎么学方案", "d08")]


@dataclass
class Document:
    doc_id: str
    title: str
    text: str
    keywords: list
    updated_days_ago: int


def tokenize(text: str) -> list:
    chars = [c for c in text if not c.isspace()]
    return chars + ["".join(chars[i:i + 2]) for i in range(len(chars) - 1)]


def embed(text: str) -> list:
    vec = [0.0] * EMBED_DIM  # 哈希 embedding:md5 定桶 + 随机符号,最后 L2 归一化
    for tok in tokenize(text):
        dg = hashlib.md5(tok.encode("utf-8")).digest()
        vec[int.from_bytes(dg[:4], "little") % EMBED_DIM] += 1.0 if dg[4] % 2 == 0 else -1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list, b: list) -> float:
    return sum(x * y for x, y in zip(a, b))  # 已归一化,点积即余弦


class VectorStore:
    def __init__(self, docs: list):  # 极简内存向量库:建库编码,检索算余弦 top-k
        self.items = [(d, embed(d.title + "。" + d.text)) for d in docs]

    def search(self, query: str, k: int = 3) -> list:
        scored = [(d, cosine(embed(query), v)) for d, v in self.items]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


def mmr_search(store: VectorStore, query: str, k: int = 3, lambda_param: float = 0.5) -> list:
    """贪心选取:每轮挑 lambda*相关性 - (1-lambda)*冗余度 最大的候选。"""
    qv = embed(query)
    pool = [(d, v, cosine(qv, v)) for d, v in store.items]
    selected = []
    while pool and len(selected) < k:
        def mmr_score(item):
            red = max((cosine(item[1], sv) for _, sv, _ in selected), default=0.0)
            return lambda_param * item[2] - (1 - lambda_param) * red
        best = max(pool, key=mmr_score)
        selected.append(best)
        pool = [c for c in pool if c[0].doc_id != best[0].doc_id]
    return [(d, rel) for d, _, rel in selected]


def rerank(results: list, query: str, alpha=0.6, beta=0.25, gamma=0.15, tau=30.0) -> list:
    """交叉特征重排:final = alpha*语义 + beta*主题词命中 + gamma*新鲜度。"""
    reranked = []
    for doc, sem in results:
        kw = sum(1 for k_ in doc.keywords if k_ in query) / max(len(doc.keywords), 1)
        fresh = math.exp(-doc.updated_days_ago / tau)  # 指数衰减,越新越接近 1
        reranked.append((doc, alpha * sem + beta * kw + gamma * fresh))
    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked


class CangjingRetriever:
    """黑糖资料室检索管线:三档策略 plain / mmr / full,共用一个向量库。"""

    def __init__(self, docs: list, threshold: float = SCORE_THRESHOLD,
                 lambda_param: float = 0.5, pool_size: int = 6):
        self.store = VectorStore(docs)
        self.threshold, self.lambda_param, self.pool_size = threshold, lambda_param, pool_size

    def retrieve(self, query: str, k: int = 3, strategy: str = "full") -> tuple:
        # 返回 (保留结果, 被阈值丢弃结果);召回取 pool_size 个,逐段加工后截前 k
        if strategy == "plain":
            return self.store.search(query, k=k), []
        cands = mmr_search(self.store, query, k=self.pool_size, lambda_param=self.lambda_param)
        kept = [(d, s) for d, s in cands if s >= self.threshold]  # 过滤必须在重排前做
        dropped = [(d, s) for d, s in cands if s < self.threshold]
        if strategy == "mmr":
            return kept[:k], dropped
        return rerank(kept, query)[:k], dropped


def evaluate(retriever: CangjingRetriever, strategy: str, k: int = 3) -> float:
    hits = 0  # 命中率@k:期望文档进前 k 即命中,返回命中比例
    for query, expected in EVAL_SET:
        kept, _ = retriever.retrieve(query, k=k, strategy=strategy)
        hits += expected in [d.doc_id for d, _ in kept]
    return hits / len(EVAL_SET)


def main() -> None:
    docs = [Document(i, t, x, k_.split(","), d) for i, t, x, k_, d in RAW_DOCS]
    retriever = CangjingRetriever(docs)
    print("=== 黑糖资料室 · 检索策略总评测 ===")
    for strategy in ("plain", "mmr", "full"):
        print(f"策略 {strategy:5s} 命中率@1 = {evaluate(retriever, strategy, k=1):.0%}")
    kept, _ = retriever.retrieve("文档切分查询改写怎么练", k=3, strategy="full")
    print("[演示] 查询:文档切分查询改写怎么练")
    for rank, (doc, score) in enumerate(kept, 1):
        print(f"TOP{rank} {doc.title} final={score:.4f}")
    print("黑糖资料室检索管线就绪")


if __name__ == "__main__":
    main()
