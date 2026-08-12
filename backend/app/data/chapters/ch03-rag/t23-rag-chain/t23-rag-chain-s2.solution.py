"""黑糖资料室第 2 步:本地 Embedding 与向量检索。

不下载任何模型,用「字符 n-gram + 哈希映射」把文本编码成向量,
再用余弦相似度做 top-k 检索——一台离线机器就能跑的最小检索器。
"""
import zlib

import numpy as np

CHUNK_SIZE = 60
CHUNK_OVERLAP = 15
EMBED_DIM = 512  # 哈希向量的维度
TOP_K = 3

# 黑糖资料室参考资料总目(第 1 步成果,原样保留)
DOCUMENTS = [
    {
        "doc_id": "yjj",
        "source": "《文档切分指南·第一章》",
        "content": "文档切分指南是资料组的核心文档。处理前先统一编码与换行,再按标题、段落和长度边界切分。初学者不要只追求切块数量:片段过短会丢失上下文,片段过长会降低检索精度。每次调整参数后都应保存样例并复查引用是否仍能回到原文。",
    },
    {
        "doc_id": "jy",
        "source": "《检索基础指南·总纲》",
        "content": "检索基础指南强调召回稳定性。查询进入系统后先规范化文本,再从索引中取得候选片段。候选不足时应记录未命中的查询,而不是让生成模型补写事实。资料组、开发组和测试组分别维护数据、实现与回归样例。",
    },
    {
        "doc_id": "dg",
        "source": "《重排设计指南》",
        "content": "重排设计指南介绍如何把更相关的候选放到前面。先保留召回阶段的候选集,再结合关键词覆盖、来源质量和位置特征计算分数。同分结果使用稳定的文档编号排序,避免多次运行顺序漂移。",
    },
    {
        "doc_id": "qk",
        "source": "《黑糖资料室·检索设计》",
        "content": "黑糖资料室采用分层检索设计,共分数据加载、文本切分、候选召回、结果重排与引用生成五层。其要义是让回答始终能回到原始资料。第一层负责统一格式,第二层保留上下文边界,后续层逐步提高相关性。若跳过数据质量检查直接生成回答,结果容易失去可靠来源。",
    },
]


def chunk_documents(documents, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """第 1 步成果:参考资料切块,出处元数据随切片走。"""
    chunks, step = [], max(chunk_size - overlap, 1)
    for doc in documents:
        text = doc["content"]
        for start in range(0, len(text), step):
            piece = text[start:start + chunk_size]
            chunks.append({"text": piece, "source": doc["source"], "doc_id": doc["doc_id"]})
    return chunks


class LocalEmbedder:
    """纯本地 embedding:单字/双字 token 经 crc32 哈希到固定维度,无需联网。"""

    def __init__(self, dim=EMBED_DIM, ngram=(1, 2)):
        self.dim = dim
        self.ngram = ngram

    def embed(self, text):
        vec = np.zeros(self.dim, dtype=np.float32)
        for n in self.ngram:
            for i in range(len(text) - n + 1):
                token = text[i:i + n]
                idx = zlib.crc32(token.encode("utf-8")) % self.dim  # 确定性哈希定桶
                vec[idx] += 1.0  # 同一 token 反复出现则累加,体现词频
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec  # L2 归一化:此后点积即余弦相似度

    def embed_all(self, texts): return np.stack([self.embed(t) for t in texts])


class VectorStore:
    """极简向量库:存 numpy 矩阵,用余弦相似度做 top-k 检索。"""

    def __init__(self, embedder):
        self.embedder = embedder
        self.chunks = []
        self.matrix = None

    def add(self, chunks):
        self.chunks = chunks
        self.matrix = self.embedder.embed_all([c["text"] for c in chunks])

    def search(self, query, top_k=TOP_K):
        """返回 [(chunk, score), ...],按余弦相似度从高到低排序。"""
        q = self.embedder.embed(query)
        scores = self.matrix @ q  # 归一化向量的点积 = 余弦相似度,一次矩阵乘算完全库
        order = np.argsort(scores)[::-1][:top_k]
        return [(self.chunks[i], float(scores[i])) for i in order]


def main():
    chunks = chunk_documents(DOCUMENTS)
    store = VectorStore(LocalEmbedder())
    store.add(chunks)
    print(f"黑糖资料室索引就绪:{len(DOCUMENTS)} 部操作指南,{len(chunks)} 个片段\n")
    question = "初学者练文档切分指南要注意什么?"
    print(f"问:{question}")
    for chunk, score in store.search(question):
        print(f"  [{score:.4f}] {chunk['source']}: {chunk['text'][:24]}...")


if __name__ == "__main__":
    main()
