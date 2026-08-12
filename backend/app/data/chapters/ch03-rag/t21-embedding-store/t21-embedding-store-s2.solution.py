"""黑糖资料室 · 第 2 步:创建 ChromaDB 集合,把 TF-IDF 向量写入向量库"""
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
    {"title": "检索基础指南", "category": "基础指南", "text": "输入表达可以变化，核心语义应保持稳定。索引构建完成后，应使用固定查询集验证召回结果。"},
    {"title": "数据清洗手册", "category": "基础指南", "text": "清理冗余信息，补足缺失字段，并统一编码、日期与枚举值。"},
    {"title": "检索设计指南", "category": "技术文档", "text": "通过候选召回、相关性重排与引用定位，提高资料问答的可靠性"},
    {"title": "重排设计指南", "category": "检索工程", "text": "减少无效规则，优先识别相关信号，并使用稳定排序避免结果漂移。"},
    {"title": "引用规范", "category": "检索工程", "text": "回答中的事实必须标注来源编号，且编号能够回到原始文档。"},
    {"title": "故障恢复指南", "category": "运行保障", "text": "服务异常时先记录错误，再按重试、降级与状态恢复顺序处理。"},
    {"title": "查询改写手册", "category": "检索工程", "text": "查询改写应保留原意，并补充能提高召回率的同义表达。"},
    {"title": "文档切分指南", "category": "检索工程", "text": "按标题、段落与长度边界切分文档，并保留必要的上下文重叠。"},
]


def main():
    # 1) 用第 1 步的嵌入器把参考资料正文变成向量
    embedder = TfidfEmbedder(n=2)
    corpus = [d["title"] + "。" + d["text"] for d in SCRIPTURES]
    embedder.fit(corpus)
    doc_vecs = embedder.encode(corpus)

    # 2) 创建内存模式的 ChromaDB 客户端与集合
    #    EphemeralClient 不落盘,适合沙箱;生产环境换 PersistentClient(path=...) 即可
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(
        name="cangjingge",
        metadata={"hnsw:space": "cosine"},  # 用余弦距离,与归一化向量配套
    )

    # 3) 显式传入 embeddings=,绕过内置(需要下载模型的)embedding function
    ids = [f"js-{i:03d}" for i in range(len(SCRIPTURES))]
    collection.add(
        ids=ids,
        embeddings=doc_vecs.tolist(),  # numpy 矩阵先转 list[list[float]]
        documents=corpus,
        metadatas=[{"title": d["title"], "category": d["category"]} for d in SCRIPTURES],
    )

    print(f"集合名称: {collection.name}")
    print(f"已写入: {collection.count()} 条操作指南")
    peek = collection.get(ids=[ids[0]], include=["metadatas"])
    print(f"抽查第一条 metadata: {peek['metadatas'][0]}")


if __name__ == "__main__":
    main()