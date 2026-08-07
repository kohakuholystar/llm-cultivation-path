"""藏经阁 · 第 5 步:语义检索 —— 查询向量化、Top-K 召回与元数据过滤"""
import re
import hashlib

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


def doc_id(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


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


def build_collection(collection, embedder, docs):
    """用第 4 步的哈希 ID 把秘籍 upsert 进集合(幂等,重复执行也安全)。"""
    for d in docs:
        text = d["title"] + "。" + d["text"]
        collection.upsert(ids=[doc_id(text)], embeddings=embedder.encode([text]).tolist(),
                          documents=[text], metadatas=[{"title": d["title"], "category": d["category"]}])


def search(collection, embedder, query, top_k=3, category=None):
    """检索三部曲:查询向量化 -> collection.query -> 距离换算成相似度。"""
    q_vec = embedder.encode([query]).tolist()
    # TODO: 用 collection.query 召回 top_k,并把余弦距离换算成相似度组装结果。
    # 提示: result = collection.query(
    #         query_embeddings=q_vec, n_results=top_k,
    #         where={"category": category} if category else None,  # 元数据预过滤
    #         include=["metadatas", "distances"])
    #       for meta, dist in zip(result["metadatas"][0], result["distances"][0]):
    #         score = round(1.0 - dist, 4)  # 余弦距离 = 1 - 余弦相似度
    raise NotImplementedError("t21-embedding-store-s5 尚未实现:请按 TODO 提示补全 search 检索")


def main():
    embedder = TfidfEmbedder(n=2)
    embedder.fit([d["title"] + "。" + d["text"] for d in SCRIPTURES])
    collection = chromadb.EphemeralClient().get_or_create_collection(
        "cangjingge", metadata={"hnsw:space": "cosine"})
    build_collection(collection, embedder, SCRIPTURES)

    print("查询: 刚猛的掌法")
    for i, h in enumerate(search(collection, embedder, "刚猛的掌法"), 1):
        print(f"  TOP{i} 《{h['title']}》[{h['category']}] 相似度 {h['score']}")

    print("查询: 以柔克刚 (限定剑法类目)")
    for i, h in enumerate(search(collection, embedder, "以柔克刚", category="剑法"), 1):
        print(f"  TOP{i} 《{h['title']}》[{h['category']}] 相似度 {h['score']}")


if __name__ == "__main__":
    main()
