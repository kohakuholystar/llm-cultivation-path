"""藏经阁 · t22-s2:MMR 去冗余 —— 纯相似度 vs 最大边际相关性对比。"""
import hashlib
import math
from dataclasses import dataclass

EMBED_DIM = 512

RAW_DOCS = [
    ("d01", "凌波微步·卷一", "凌波微步乃逍遥派轻功,步法依周易六十四卦方位变化,踏水而行不湿鞋袜。", "轻功,步法,逍遥派", 3),
    ("d02", "凌波微步·卷二", "凌波微步卷二补述步法变化,依周易卦象踏位,内力绵长者可避暗器。", "轻功,内力", 40),
    ("d03", "水上漂心法", "水上漂讲究提气轻身,足尖点水借力而行,需十年桩功打底。", "轻功,水上漂,身法", 5),
    ("d04", "铁掌功", "铁掌功掌力刚猛,开碑裂石,裘千仞以此掌法名震江湖。", "掌法,刚猛", 120),
    ("d05", "火焰刀", "火焰刀以无形刀气伤人,出招时掌心灼热如火,乃密宗绝学。", "刀法,掌法,密宗", 200),
    ("d06", "九阳疗伤篇", "九阳神功疗伤篇,气走任督,可解寒毒,内伤自愈。", "疗伤,内功", 10),
    ("d07", "暴雨梨花针", "暴雨梨花针乃唐门暗器,二十七枚银针激射而出,避无可避。", "暗器,唐门", 60),
    ("d08", "基础剑法图解", "剑法入门图解,刺撩劈扫四式,配图三十幅,适合初学。", "剑法,入门", 2),
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

    冗余度 = 候选与已选集里任何一卷的最大余弦相似度。
    lambda 越靠近 1 越像纯相似度,越靠近 0 越追求多样。
    """
    qv = embed(query)
    pool = [(d, v, cosine(qv, v)) for d, v in store.items]
    selected = []
    while pool and len(selected) < k:
        # TODO: 从 pool 里选出 mmr 分最高的候选,加入 selected 并移出 pool。
        # 提示: 内层 def mmr_score(item):
        #         _, v, rel = item
        #         redundancy = max((cosine(v, sv) for _, sv, _ in selected), default=0.0)
        #         return lambda_param * rel - (1 - lambda_param) * redundancy
        #       best = max(pool, key=mmr_score);selected.append(best)
        #       pool = [c for c in pool if c[0].doc_id != best[0].doc_id]
        raise NotImplementedError("t22-retrieval-rerank-s2 尚未实现:请按 TODO 提示补全 mmr_search 贪心循环")
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
    query = "凌波微步怎么练"
    print(f"[查询] {query}")
    show("纯相似度 TOP3", store.search(query, k=3))
    show("MMR(lambda=0.5) TOP3", mmr_search(store, query, k=3, lambda_param=0.5))


if __name__ == "__main__":
    main()
