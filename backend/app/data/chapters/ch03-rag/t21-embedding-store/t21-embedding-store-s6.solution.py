"""藏经阁 · 第 6 步:封装 ScriptureStore —— 一个可复用的向量入库组件"""
import re, hashlib

import numpy as np
import chromadb


def char_ngrams(text, n=2):
    text = re.sub(r"\s+", "", text)
    return [text[i:i + n] for i in range(max(len(text) - n + 1, 1))]


class TfidfEmbedder:
    """极简 TF-IDF 嵌入器,接口对齐 sentence-transformers 的 encode()。"""

    def __init__(self, n=2):
        self.n, self.vocab, self.idf = n, {}, None

    def fit(self, texts):
        df = {}
        for t in texts:
            for tok in set(char_ngrams(t, self.n)):
                df[tok] = df.get(tok, 0) + 1
        tokens = sorted(df)
        self.vocab = {tok: i for i, tok in enumerate(tokens)}
        self.idf = np.array([np.log((1 + len(texts)) / (1 + df[t])) + 1.0 for t in tokens])
        return self

    def encode(self, texts):
        if self.idf is None:
            raise RuntimeError("请先调用 fit() 或 build_index()")
        mat = np.zeros((len(texts), len(self.vocab)))
        for row, t in enumerate(texts):
            for tok in char_ngrams(t, self.n):
                if tok in self.vocab:
                    mat[row, self.vocab[tok]] += 1.0
        mat *= self.idf
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        return mat / norms


def doc_id(text):  # 内容寻址 ID:同一段经文永远同一个 ID,入库天然幂等
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


class ScriptureStore:
    """藏经阁向量库:建索引、增量同步、语义检索一站封装(替换点:Client 与 Embedder)。"""

    def __init__(self, name="cangjingge", ngram=2):
        self.collection = chromadb.EphemeralClient().get_or_create_collection(
            name, metadata={"hnsw:space": "cosine"})
        self.embedder = TfidfEmbedder(n=ngram)

    @staticmethod
    def _full_text(d):
        return d["title"] + "。" + d["text"]

    def build_index(self, docs, batch_size=4):
        """首次建库:fit 词表,然后分批 upsert,返回总条数。"""
        texts = [self._full_text(d) for d in docs]
        self.embedder.fit(texts)
        vecs = self.embedder.encode(texts).tolist()
        for start in range(0, len(docs), batch_size):
            batch = docs[start:start + batch_size]
            self.collection.upsert(
                ids=[doc_id(self._full_text(d)) for d in batch],
                embeddings=vecs[start:start + batch_size],
                documents=texts[start:start + batch_size],
                metadatas=[{"title": d["title"], "category": d["category"]} for d in batch])
        return self.collection.count()

    def sync(self, docs):
        """增量同步:哈希去重,修订版先删后写,返回入库报告。"""
        report = {"新增": 0, "更新": 0, "跳过": 0}
        for d in docs:
            text = self._full_text(d)
            did = doc_id(text)
            if self.collection.get(ids=[did], include=[])["ids"]:
                report["跳过"] += 1  # 内容一字未变
                continue
            old = self.collection.get(where={"title": d["title"]}, include=[])
            if old["ids"]:  # 同书名不同哈希 = 修订版
                self.collection.delete(ids=old["ids"])
                report["更新"] += 1
            else:
                report["新增"] += 1
            meta = {"title": d["title"], "category": d["category"]}
            self.collection.upsert(ids=[did], embeddings=self.embedder.encode([text]).tolist(),
                                   documents=[text], metadatas=[meta])
        return report

    def search(self, query, top_k=3, category=None):
        """语义检索:查询向量化 -> Top-K -> 余弦距离换算成相似度。"""
        result = self.collection.query(
            query_embeddings=self.embedder.encode([query]).tolist(),
            n_results=top_k, where={"category": category} if category else None,
            include=["metadatas", "distances"])
        return [{"title": m["title"], "score": round(1.0 - dist, 4)}
                for m, dist in zip(result["metadatas"][0], result["distances"][0])]


def main():
    scriptures = [
        {"title": "九阳神功", "category": "内功", "text": "他强由他强，清风拂山岗。九阳真气生生不息，乃内功之正宗"},
        {"title": "九阴真经", "category": "内功", "text": "天之道，损有余而补不足。九阴真经总纲以柔克刚，载有疗伤之篇"},
        {"title": "独孤九剑", "category": "剑法", "text": "无招胜有招，料敌机先。破剑破刀破枪，天下剑法皆可破"},
        {"title": "太极剑", "category": "剑法", "text": "以柔克刚，以静制动。剑意连绵不绝，如长江大河"},
        {"title": "降龙十八掌", "category": "掌法", "text": "亢龙有悔，盈不可久。掌法刚猛，招式简明而威力无穷"},
        {"title": "凌波微步", "category": "轻功", "text": "步法依易经六十四卦方位变化，动无常则，若危若安"},
    ]
    store = ScriptureStore()
    print(f"建库完成: {store.build_index(scriptures)} 条秘籍")
    updates = [scriptures[0], {"title": "神照经", "category": "内功", "text": "神照功内力浑厚，有起死回生之效"}]  # 1 重复 1 新增
    print(f"增量同步报告: {store.sync(updates)}")
    for i, h in enumerate(store.search("刚猛的武功", top_k=2), 1):
        print(f"  TOP{i} 《{h['title']}》 相似度 {h['score']}")


if __name__ == "__main__":
    main()