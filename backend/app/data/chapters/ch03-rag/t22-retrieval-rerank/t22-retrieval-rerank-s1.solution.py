"""黑糖资料室 · t22-s1:相似度检索基线
延续 t21 的本地 embedding 方案:字符 n-gram 哈希向量,纯本地计算,不下载任何模型。
"""
import hashlib
import math
from dataclasses import dataclass

EMBED_DIM = 512  # 哈希向量维度,越大碰撞越少

# (编号, 标题, 正文, 主题词, 距今更新天数) —— 后几步的特征全靠后两列
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
    """一篇文档:正文 + 主题词 + 更新天数,后几步的交叉特征都挂在上面。"""
    doc_id: str
    title: str
    text: str
    keywords: list
    updated_days_ago: int


def make_docs() -> list:
    return [Document(i, t, x, k.split(","), d) for i, t, x, k, d in RAW_DOCS]


def tokenize(text: str) -> list:
    """字符 unigram + bigram:中文按字切,天然免分词器。"""
    chars = [c for c in text if not c.isspace()]
    return chars + ["".join(chars[i:i + 2]) for i in range(len(chars) - 1)]


def embed(text: str) -> list:
    """哈希 embedding:token 投到固定维度并带随机符号,最后 L2 归一化。"""
    vec = [0.0] * EMBED_DIM
    for tok in tokenize(text):
        digest = hashlib.md5(tok.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % EMBED_DIM
        vec[idx] += 1.0 if digest[4] % 2 == 0 else -1.0  # 随机符号抵消碰撞偏差
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list, b: list) -> float:
    """两边都已归一化,点积即余弦相似度。"""
    return sum(x * y for x, y in zip(a, b))


class VectorStore:
    """极简内存向量库:建库时把 标题+正文 编码成向量,检索时算余弦 top-k。"""
    def __init__(self, docs: list):
        self.items = [(d, embed(d.title + "。" + d.text)) for d in docs]

    def search(self, query: str, k: int = 3) -> list:
        qv = embed(query)
        scored = [(d, cosine(qv, v)) for d, v in self.items]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


def main() -> None:
    store = VectorStore(make_docs())
    query = "如何按段落切分并保留上下文"
    print(f"[查询] {query}")
    for rank, (doc, score) in enumerate(store.search(query, k=3), 1):
        print(f"TOP{rank} {doc.title} score={score:.4f}")


if __name__ == "__main__":
    main()
