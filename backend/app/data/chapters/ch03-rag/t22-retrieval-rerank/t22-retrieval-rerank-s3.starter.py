"""黑糖资料室 · t22-s3:score 阈值过滤 —— 低分结果宁可丢弃,也不塞给下游。"""
# 学习契约
# 目标：完成 t22-retrieval-rerank-s3 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 4 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：make_docs() -> list; tokenize(text) -> list; embed(text) -> list; cosine(a, b) -> float。
# 技术栈：hashlib, math, dataclasses。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
import hashlib
import math
from dataclasses import dataclass

EMBED_DIM = 512
SCORE_THRESHOLD = 0.12  # 余弦相似度及格线:低于它的候选视为「馆里没这本书」

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


def filter_by_threshold(results: list, threshold: float = SCORE_THRESHOLD) -> tuple:
    """把 top-k 按阈值切成 (保留, 丢弃) 两堆,分数不达标的一律不进下游。"""
    # TODO: 把 results 按 threshold 切成 (kept, dropped) 两个列表并返回。
    #       kept    = 分数 >= threshold 的 (doc, score)
    #       dropped = 分数 <  threshold 的 (doc, score)
    # 提示: kept = [(d, s) for d, s in results if s >= threshold]
    #       dropped = [(d, s) for d, s in results if s < threshold]
    raise NotImplementedError("t22-retrieval-rerank-s3 尚未实现:请按 TODO 提示补全 filter_by_threshold")


def answer(store: VectorStore, query: str) -> None:
    print(f"[查询] {query}")
    kept, dropped = filter_by_threshold(store.search(query, k=3))
    for rank, (doc, score) in enumerate(kept, 1):
        print(f"TOP{rank} {doc.title} score={score:.4f}")
    for doc, score in dropped:
        print(f"  [丢弃] {doc.title} score={score:.4f} 低于阈值 {SCORE_THRESHOLD}")
    # TODO: 当 kept 为空时,打印兜底话术「未找到可靠结果:请换个说法,或转人工查阅。」
    #       提示:if not kept:
    raise NotImplementedError("t22-retrieval-rerank-s3 尚未实现:请按 TODO 提示补全空结果兜底")


def main() -> None:
    store = VectorStore(make_docs())
    answer(store, "如何按段落切分并保留上下文")
    answer(store, "今天中午吃什么外卖")  # 馆外问题:应该全部被阈值拦下


if __name__ == "__main__":
    main()
