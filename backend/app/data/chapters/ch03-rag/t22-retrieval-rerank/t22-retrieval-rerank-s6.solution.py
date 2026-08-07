"""藏经阁 · t22-s6:检索管线总装 —— 向量检索 -> MMR -> 阈值过滤 -> 重排序,并做三策略总评测。"""
import hashlib
import math
from dataclasses import dataclass

EMBED_DIM, SCORE_THRESHOLD = 512, 0.12

RAW_DOCS = [  # (编号, 经名, 正文, 主题词, 距今更新天数)
    ("d01", "凌波微步·卷一", "凌波微步乃逍遥派轻功,步法依周易六十四卦方位变化,踏水而行不湿鞋袜。", "轻功,步法,逍遥派", 3),
    ("d02", "凌波微步·卷二", "凌波微步卷二补述步法变化,依周易卦象踏位,内力绵长者可避暗器。", "轻功,内力", 40),
    ("d03", "水上漂心法", "水上漂讲究提气轻身,足尖点水借力而行,需十年桩功打底。", "轻功,水上漂,身法", 5),
    ("d04", "铁掌功", "铁掌功掌力刚猛,开碑裂石,裘千仞以此掌法名震江湖。", "掌法,刚猛", 120),
    ("d05", "火焰刀", "火焰刀以无形刀气伤人,出招时掌心灼热如火,乃密宗绝学。", "刀法,掌法,密宗", 200),
    ("d06", "九阳疗伤篇", "九阳神功疗伤篇,气走任督,可解寒毒,内伤自愈。", "疗伤,内功", 10),
    ("d07", "暴雨梨花针", "暴雨梨花针乃唐门暗器,二十七枚银针激射而出,避无可避。", "暗器,唐门", 60),
    ("d08", "基础剑法图解", "剑法入门图解,刺撩劈扫四式,配图三十幅,适合初学。", "剑法,入门", 2),
]
EVAL_SET = [("如何练成踏水而行的轻功", "d01"), ("刚猛的掌法绝学", "d04"),  # 标注集
            ("中了寒毒如何疗伤", "d06"), ("踏水而行能躲开唐门暗器吗", "d07"), ("初学者怎么学剑", "d08")]


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
    """藏经阁检索管线:三档策略 plain / mmr / full,共用一个向量库。"""

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
    hits = 0  # 命中率@k:期望经书进前 k 即命中,返回命中比例
    for query, expected in EVAL_SET:
        kept, _ = retriever.retrieve(query, k=k, strategy=strategy)
        hits += expected in [d.doc_id for d, _ in kept]
    return hits / len(EVAL_SET)


def main() -> None:
    docs = [Document(i, t, x, k_.split(","), d) for i, t, x, k_, d in RAW_DOCS]
    retriever = CangjingRetriever(docs)
    print("=== 藏经阁 · 检索策略总评测 ===")
    for strategy in ("plain", "mmr", "full"):
        print(f"策略 {strategy:5s} 命中率@1 = {evaluate(retriever, strategy, k=1):.0%}")
    kept, _ = retriever.retrieve("轻功水上漂怎么练", k=3, strategy="full")
    print("[演示] 查询:轻功水上漂怎么练")
    for rank, (doc, score) in enumerate(kept, 1):
        print(f"TOP{rank} {doc.title} final={score:.4f}")
    print("藏经阁检索管线就绪")


if __name__ == "__main__":
    main()
