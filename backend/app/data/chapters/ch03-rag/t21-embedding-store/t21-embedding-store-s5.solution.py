"""黑糖资料室 · 第 5 步:语义检索 —— 查询向量化、Top-K 召回与元数据过滤"""
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
    {"title": "检索基础指南", "category": "基础指南", "text": "输入表达可以变化，核心语义应保持稳定。索引构建完成后，应使用固定查询集验证召回结果。"},
    {"title": "数据清洗手册", "category": "基础指南", "text": "清理冗余信息，补足缺失字段，并统一编码、日期与枚举值。"},
    {"title": "检索设计指南", "category": "技术文档", "text": "通过候选召回、相关性重排与引用定位，提高资料问答的可靠性"},
    {"title": "重排设计指南", "category": "检索工程", "text": "减少无效规则，优先识别相关信号，并使用稳定排序避免结果漂移。"},
    {"title": "引用规范", "category": "检索工程", "text": "回答中的事实必须标注来源编号，且编号能够回到原始文档。"},
    {"title": "故障恢复指南", "category": "运行保障", "text": "服务异常时先记录错误，再按重试、降级与状态恢复顺序处理。"},
    {"title": "查询改写手册", "category": "检索工程", "text": "查询改写应保留原意，并补充能提高召回率的同义表达。"},
    {"title": "文档切分指南", "category": "检索工程", "text": "按标题、段落与长度边界切分文档，并保留必要的上下文重叠。"},
]


def build_collection(collection, embedder, docs):
    """用第 4 步的哈希 ID 把参考资料 upsert 进集合(幂等,重复执行也安全)。"""
    for d in docs:
        text = d["title"] + "。" + d["text"]
        collection.upsert(ids=[doc_id(text)], embeddings=embedder.encode([text]).tolist(),
                          documents=[text], metadatas=[{"title": d["title"], "category": d["category"]}])


def search(collection, embedder, query, top_k=3, category=None):
    """检索三部曲:查询向量化 -> collection.query -> 距离换算成相似度。"""
    q_vec = embedder.encode([query]).tolist()
    result = collection.query(
        query_embeddings=q_vec,
        n_results=top_k,
        where={"category": category} if category else None,  # 元数据预过滤
        include=["metadatas", "distances"],
    )
    hits = []
    for meta, dist in zip(result["metadatas"][0], result["distances"][0]):
        hits.append({"title": meta["title"], "category": meta["category"],
                     "score": round(1.0 - dist, 4)})  # 余弦距离 = 1 - 余弦相似度
    return hits


def main():
    embedder = TfidfEmbedder(n=2)
    embedder.fit([d["title"] + "。" + d["text"] for d in SCRIPTURES])
    collection = chromadb.EphemeralClient().get_or_create_collection(
        "cangjingge", metadata={"hnsw:space": "cosine"})
    build_collection(collection, embedder, SCRIPTURES)

    print("查询: 稳定的处理方法")
    for i, h in enumerate(search(collection, embedder, "稳定的处理方法"), 1):
        print(f"  TOP{i} 《{h['title']}》[{h['category']}] 相似度 {h['score']}")

    print("查询: 优先保留相关信号 (限定创作方法类目)")
    for i, h in enumerate(search(collection, embedder, "优先保留相关信号", category="创作方法"), 1):
        print(f"  TOP{i} 《{h['title']}》[{h['category']}] 相似度 {h['score']}")


if __name__ == "__main__":
    main()