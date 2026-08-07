"""藏经阁第 2 步:本地 Embedding 与向量检索。

不下载任何模型,用「字符 n-gram + 哈希映射」把文本编码成向量,
再用余弦相似度做 top-k 检索——一台离线机器就能跑的最小检索器。
"""
import zlib

import numpy as np

CHUNK_SIZE = 60
CHUNK_OVERLAP = 15
EMBED_DIM = 512  # 哈希向量的维度
TOP_K = 3

# 藏经阁秘籍总目(第 1 步成果,原样保留)
DOCUMENTS = [
    {
        "doc_id": "yjj",
        "source": "《易筋经·卷一》",
        "content": "易筋经乃少林镇寺之宝,讲究以意导气、以气运力。修习者需每日寅时起身,面东而立,先行吐纳三十六次,再依图谱摆出十二式桩架。初学者切忌贪快,桩架不正则气行偏差,轻则筋骨酸痛,重则伤及经络。经中明言:宁可十日不进阶,不可一日错行功。",
    },
    {
        "doc_id": "jy",
        "source": "《九阳真经·总纲》",
        "content": "九阳真经重在内力生生不息。其总纲云:他强由他强,清风拂山岗。修习九阳神功者,内力自行周天运转,寒暑不侵,百毒难伤。然此功进境极缓,非有大毅力者不能成。觉远大师于华山之巅口述此经,张君宝与郭襄各得一部分,后衍化为武当、峨眉两派内功根基。",
    },
    {
        "doc_id": "dg",
        "source": "《独孤九剑·剑理篇》",
        "content": "独孤九剑共九式,破尽天下武功。其核心剑理只有四个字:料敌机先。风清扬传令狐冲时言:剑招是死的,人是活的,无招胜有招。破剑式用以破解各派剑法,破刀式克制单刀双刀,破气式则专克内功深厚的对手。习此剑者须忘却固定招式,只记剑意。",
    },
    {
        "doc_id": "qk",
        "source": "《乾坤大挪移·心法》",
        "content": "乾坤大挪移为明教镇教神功,共分七层。其要义在于激发人体潜力、挪移乾坤二气。第一层需七年苦修,第二层加倍,层层递进。张无忌因身具九阳神功,内力深厚,方能在密道中速成。此功最忌根基不牢而强行冲关,历代教主多有因此殒命者。",
    },
]


def chunk_documents(documents, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """第 1 步成果:秘籍切块,出处元数据随切片走。"""
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
    print(f"藏经阁索引就绪:{len(DOCUMENTS)} 部秘籍,{len(chunks)} 个片段\n")
    question = "初学者练易筋经要注意什么?"
    print(f"问:{question}")
    for chunk, score in store.search(question):
        print(f"  [{score:.4f}] {chunk['source']}: {chunk['text'][:24]}...")


if __name__ == "__main__":
    main()
