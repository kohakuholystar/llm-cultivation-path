"""藏经阁 · t22-s1:相似度检索基线
延续 t21 的本地 embedding 方案:字符 n-gram 哈希向量,纯本地计算,不下载任何模型。
"""
import hashlib
import math
from dataclasses import dataclass

EMBED_DIM = 512  # 哈希向量维度,越大碰撞越少

# (编号, 经名, 正文, 主题词, 距今更新天数) —— 后几步的特征全靠后两列
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
    """一卷经书:正文 + 主题词 + 更新天数,后几步的交叉特征都挂在上面。"""
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
    query = "如何练成踏水而行的轻功"
    print(f"[查询] {query}")
    for rank, (doc, score) in enumerate(store.search(query, k=3), 1):
        print(f"TOP{rank} {doc.title} score={score:.4f}")


if __name__ == "__main__":
    main()
