"""藏经阁 · 第 2 步:创建 ChromaDB 集合,把 TF-IDF 向量写入向量库"""
import re

import numpy as np
import chromadb


def char_ngrams(text, n=2):
    """把文本切成字符 n-gram(与第 1 步一致的嵌入器,此处直接复用)。"""
    text = re.sub(r"\s+", "", text)
    if len(text) < n:
        return [text]
    return [text[i:i + n] for i in range(len(text) - n + 1)]


class TfidfEmbedder:
    """极简 TF-IDF 嵌入器,接口对齐 sentence-transformers 的 encode()。"""

    def __init__(self, n=2):
        self.n = n
        self.vocab = {}
        self.idf = None

    def fit(self, texts):
        df = {}
        for t in texts:
            for tok in set(char_ngrams(t, self.n)):
                df[tok] = df.get(tok, 0) + 1
        tokens = sorted(df)
        self.vocab = {tok: i for i, tok in enumerate(tokens)}
        n_docs = len(texts)
        self.idf = np.array([np.log((1 + n_docs) / (1 + df[t])) + 1.0 for t in tokens])
        return self

    def encode(self, texts):
        if self.idf is None:
            raise RuntimeError("请先调用 fit() 构建词表与 IDF")
        mat = np.zeros((len(texts), len(self.vocab)))
        for row, t in enumerate(texts):
            for tok in char_ngrams(t, self.n):
                if tok in self.vocab:
                    mat[row, self.vocab[tok]] += 1.0
        mat *= self.idf
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        return mat / norms


SCRIPTURES = [
    {"title": "九阳神功", "category": "内功", "text": "他强由他强，清风拂山岗。九阳真气生生不息，乃内功之正宗"},
    {"title": "九阴真经", "category": "内功", "text": "天之道，损有余而补不足。九阴真经总纲以柔克刚，载有疗伤之篇"},
    {"title": "乾坤大挪移", "category": "内功", "text": "激发自身潜力，牵引挪移敌劲，阴阳二气转换自如"},
    {"title": "独孤九剑", "category": "剑法", "text": "无招胜有招，料敌机先。破剑破刀破枪，天下剑法皆可破"},
    {"title": "太极剑", "category": "剑法", "text": "以柔克刚，以静制动。剑意连绵不绝，如长江大河"},
    {"title": "降龙十八掌", "category": "掌法", "text": "亢龙有悔，盈不可久。掌法刚猛，招式简明而威力无穷"},
    {"title": "黯然销魂掌", "category": "掌法", "text": "黯然销魂者，唯别而已矣。掌力随心境而生，情深则力深"},
    {"title": "凌波微步", "category": "轻功", "text": "步法依易经六十四卦方位变化，动无常则，若危若安"},
]


def main():
    # 1) 用第 1 步的嵌入器把秘籍正文变成向量
    embedder = TfidfEmbedder(n=2)
    corpus = [d["title"] + "。" + d["text"] for d in SCRIPTURES]
    embedder.fit(corpus)
    doc_vecs = embedder.encode(corpus)

    # 2) 创建内存模式的 ChromaDB 客户端与集合
    #    EphemeralClient 不落盘,适合沙箱;生产环境换 PersistentClient(path=...) 即可
    client = chromadb.EphemeralClient()
    # TODO: 创建集合并赋值给 collection。
    # 提示: collection = client.get_or_create_collection(name="cangjingge",
    #       metadata={"hnsw:space": "cosine"})  # 用余弦距离,与归一化向量配套
    raise NotImplementedError("t21-embedding-store-s2 尚未实现:请按 TODO 提示创建集合")

    # 3) 显式传入 embeddings=,绕过内置(需要下载模型的)embedding function
    ids = [f"js-{i:03d}" for i in range(len(SCRIPTURES))]
    # TODO: 把向量与文本一次性写入集合。
    # 提示: collection.add(ids=ids, embeddings=doc_vecs.tolist(), documents=corpus,
    #       metadatas=[{"title": d["title"], "category": d["category"]} for d in SCRIPTURES])
    raise NotImplementedError("t21-embedding-store-s2 尚未实现:请按 TODO 提示写入集合")

    print(f"集合名称: {collection.name}")
    print(f"已写入: {collection.count()} 条秘籍")
    peek = collection.get(ids=[ids[0]], include=["metadatas"])
    print(f"抽查第一条 metadata: {peek['metadatas'][0]}")


if __name__ == "__main__":
    main()
