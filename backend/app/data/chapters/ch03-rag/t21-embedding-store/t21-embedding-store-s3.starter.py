"""藏经阁 · 第 3 步:批量入库 —— 分批写入,并见识重复 ID 的报错"""
import re

import numpy as np
import chromadb


def char_ngrams(text, n=2):
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
BATCH_SIZE = 3  # 模拟真实工程的分批:每批 3 条


def batch_add(collection, ids, vectors, documents, metadatas, batch_size=BATCH_SIZE):
    """分批写入向量库。真实语料可能有几百万条,一次 add 会撑爆内存/超时。"""
    total = len(ids)
    # TODO: 分批循环写入并打印批次进度。
    # 提示: for start in range(0, total, batch_size):
    #         end = min(start + batch_size, total)
    #         collection.add(ids=ids[start:end], embeddings=vectors[start:end],
    #                        documents=documents[start:end], metadatas=metadatas[start:end])
    #         print(f"  批次 {start // batch_size + 1}: 写入 {end - start} 条 (进度 {end}/{total})")
    raise NotImplementedError("t21-embedding-store-s3 尚未实现:请按 TODO 提示补全批量入库循环")


def main():
    embedder = TfidfEmbedder(n=2)
    corpus = [d["title"] + "。" + d["text"] for d in SCRIPTURES]
    embedder.fit(corpus)
    doc_vecs = embedder.encode(corpus).tolist()

    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection("cangjingge", metadata={"hnsw:space": "cosine"})

    ids = [f"js-{i:03d}" for i in range(len(SCRIPTURES))]
    metas = [{"title": d["title"], "category": d["category"]} for d in SCRIPTURES]
    print("开始批量入库:")
    batch_add(collection, ids, doc_vecs, corpus, metas)
    print(f"入库完成,集合现有 {collection.count()} 条")

    # 重复 add 同一个 id:ChromaDB 1.x 会静默忽略(不报错也不写入)
    # 看似省心,实则把数据正确性交给了默认值 —— 第 4 步我们改用内容哈希自己管控
    before = collection.count()
    collection.add(ids=[ids[0]], embeddings=[doc_vecs[0]], documents=[corpus[0]], metadatas=[metas[0]])
    print(f"重复 add 同一 ID: {before} -> {collection.count()} 条 (被静默忽略,不报错)")


if __name__ == "__main__":
    main()
