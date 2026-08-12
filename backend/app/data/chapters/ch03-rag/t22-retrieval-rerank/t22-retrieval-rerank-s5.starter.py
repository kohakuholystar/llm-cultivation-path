"""黑糖资料室 · t22-s5:检索命中率评估 —— 没有标注集的优化都是盲人摸象。"""
# 学习契约
# 目标：完成 t22-retrieval-rerank-s5 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 2 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：make_docs() -> list; tokenize(text) -> list; embed(text) -> list; cosine(a, b) -> float。
# 技术栈：hashlib, math, dataclasses。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
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

# 标注集:(query, 期望命中的文档编号) —— 评估的一切地基
EVAL_SET = [
    ("如何按段落切分并保留上下文", "d01"),
    ("稳定的错误恢复方法", "d04"),
    ("服务故障后如何恢复", "d06"),
    ("引用结果如何校验", "d07"),
    ("初学者怎么学方案", "d08"),
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


def rerank(results: list, query: str,
           alpha: float = 0.6, beta: float = 0.25, gamma: float = 0.15,
           tau: float = 30.0) -> list:
    reranked = []
    for doc, sem in results:
        hits = sum(1 for kw in doc.keywords if kw in query)
        kw_score = hits / max(len(doc.keywords), 1)
        fresh = math.exp(-doc.updated_days_ago / tau)
        final = alpha * sem + beta * kw_score + gamma * fresh
        reranked.append((doc, final, sem, kw_score, fresh))
    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked


def hit_rate_at_k(store: VectorStore, eval_set: list, k: int = 3,
                  use_rerank: bool = False) -> float:
    """命中率@k:期望文档出现在前 k 条即记命中,返回命中比例。"""
    hits = 0
    for query, expected in eval_set:
        if use_rerank:
            pool = store.search(query, k=5)  # 召回多于 k,重排才有腾挪空间
            results = [(d, s) for d, s, *_ in rerank(pool, query)][:k]
        else:
            results = store.search(query, k=k)
        got = [d.doc_id for d, _ in results]
        # TODO: 判定 expected 是否命中 got,命中则 hits += 1,并打印 HIT/MISS。
        # 提示:ok = expected in got
        #       print(f"  [{'HIT' if ok else 'MISS'}] {query} -> {got} (期望 {expected})")
        #       hits += ok  # True 会按 1 累加,不必再写 if
        raise NotImplementedError("t22-retrieval-rerank-s5 尚未实现:请按 TODO 提示补全命中判定")
    return hits / len(eval_set)


def main() -> None:
    store = VectorStore(make_docs())
    print("--- 纯相似度 ---")
    base = hit_rate_at_k(store, EVAL_SET, k=1, use_rerank=False)
    print("--- 加重排序 ---")
    mine = hit_rate_at_k(store, EVAL_SET, k=1, use_rerank=True)
    print(f"命中率@1:纯相似度={base:.0%} 加重排序={mine:.0%}")


if __name__ == "__main__":
    main()
