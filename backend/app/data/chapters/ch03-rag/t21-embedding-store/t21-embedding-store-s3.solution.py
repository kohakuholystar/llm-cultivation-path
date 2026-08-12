"""黑糖资料室 · 第 3 步:批量入库 —— 分批写入,并见识重复 ID 的报错"""
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
    {"title": "检索基础指南", "category": "基础指南", "text": "输入表达可以变化，核心语义应保持稳定。索引构建完成后，应使用固定查询集验证召回结果。"},
    {"title": "数据清洗手册", "category": "基础指南", "text": "清理冗余信息，补足缺失字段，并统一编码、日期与枚举值。"},
    {"title": "检索设计指南", "category": "技术文档", "text": "通过候选召回、相关性重排与引用定位，提高资料问答的可靠性"},
    {"title": "重排设计指南", "category": "检索工程", "text": "减少无效规则，优先识别相关信号，并使用稳定排序避免结果漂移。"},
    {"title": "引用规范", "category": "检索工程", "text": "回答中的事实必须标注来源编号，且编号能够回到原始文档。"},
    {"title": "故障恢复指南", "category": "运行保障", "text": "服务异常时先记录错误，再按重试、降级与状态恢复顺序处理。"},
    {"title": "查询改写手册", "category": "检索工程", "text": "查询改写应保留原意，并补充能提高召回率的同义表达。"},
    {"title": "文档切分指南", "category": "检索工程", "text": "按标题、段落与长度边界切分文档，并保留必要的上下文重叠。"},
]
BATCH_SIZE = 3  # 模拟真实工程的分批:每批 3 条


def batch_add(collection, ids, vectors, documents, metadatas, batch_size=BATCH_SIZE):
    """分批写入向量库。真实语料可能有几百万条,一次 add 会撑爆内存/超时。"""
    total = len(ids)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        collection.add(
            ids=ids[start:end],
            embeddings=vectors[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  批次 {start // batch_size + 1}: 写入 {end - start} 条 (进度 {end}/{total})")


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