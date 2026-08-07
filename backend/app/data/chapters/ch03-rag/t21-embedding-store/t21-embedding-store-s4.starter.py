"""藏经阁 · 第 4 步:内容哈希做 ID,实现增量更新与去重"""
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
    """内容寻址:同一段经文永远得到同一个 ID,天然幂等。"""
    # TODO: 计算内容的 sha1 摘要并截断 12 位作为 ID。
    # 提示: return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    raise NotImplementedError("t21-embedding-store-s4 尚未实现:请按 TODO 提示补全 doc_id")


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

# 藏经阁第二次送来的扫描件:1 份重复、1 份修订版、1 份新发现
SECOND_BATCH = [
    SCRIPTURES[0],  # 重复扫描的《九阳神功》,应被跳过
    {"title": "太极剑", "category": "剑法", "text": "以柔克刚，以静制动。剑意连绵不绝，如长江大河。修订:补充推手要诀"},  # 修订,应更新
    {"title": "九阳神功", "category": "内功", "text": "他强由他强，清风拂山岗。九阳真气生生不息，乃内功之正宗"},  # 又一份重复
    {"title": "神照经", "category": "内功", "text": "神照功内力浑厚，有起死回生之效，乃武林第一精纯内功"},  # 新秘籍,应新增
]


def sync_documents(collection, embedder, docs):
    """增量同步:逐条比对内容哈希,只写真正变化的文档,返回入库报告。"""
    report = {"新增": [], "更新": [], "跳过": []}
    for d in docs:
        text = d["title"] + "。" + d["text"]
        did = doc_id(text)
        # TODO: 三态判定 -> 1) get(ids=[did], include=[])["ids"] 非空则记"跳过"并 continue
        #       2) get(where={"title": ...}) 命中旧版则 delete 后记"更新",否则记"新增";最后 upsert
        # 提示: old = collection.get(where={"title": d["title"]}, include=[])
        #       vec = embedder.encode([text]).tolist()
        #       collection.upsert(ids=[did], embeddings=vec, documents=[text],
        #                         metadatas=[{"title": d["title"], "category": d["category"], "content_hash": did}])
        raise NotImplementedError("t21-embedding-store-s4 尚未实现:请按 TODO 提示补全 sync_documents 三态判定")
    return report


def main():
    embedder = TfidfEmbedder(n=2)
    embedder.fit([d["title"] + "。" + d["text"] for d in SCRIPTURES + SECOND_BATCH])

    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection("cangjingge", metadata={"hnsw:space": "cosine"})

    r1 = sync_documents(collection, embedder, SCRIPTURES)
    print(f"首次同步: 新增 {len(r1['新增'])} 条,共 {collection.count()} 条")

    r2 = sync_documents(collection, embedder, SECOND_BATCH)
    print(f"二次同步: 新增 {r2['新增']} 更新 {r2['更新']} 跳过 {r2['跳过']}")
    print(f"最终库藏: {collection.count()} 条 (8 旧 - 1 修订换版 + 1 新 = 9)")


if __name__ == "__main__":
    main()
