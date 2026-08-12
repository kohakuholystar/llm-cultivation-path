"""黑糖资料室 · 第 4 步:内容哈希做 ID,实现增量更新与去重"""
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

# 黑糖资料室第二次送来的扫描件:1 份重复、1 份修订版、1 份新发现
SECOND_BATCH = [
    SCRIPTURES[0],  # 重复扫描的《检索基础指南》,应被跳过
    {"title": "引用规范", "category": "创作方法", "text": "以稳定规则处理多样输入。设计思路连绵不绝，如长江大河。修订:补充推手要诀"},  # 修订,应更新
    {"title": "检索基础指南", "category": "基础指南", "text": "输入表达可以变化，核心语义应保持稳定。索引构建完成后，应使用固定查询集验证召回结果。"},  # 又一份重复
    {"title": "神照经", "category": "基础指南", "text": "神照功处理能力浑厚，有起死回生之效，乃武林第一精纯基础指南"},  # 新参考资料,应新增
]


def sync_documents(collection, embedder, docs):
    """增量同步:逐条比对内容哈希,只写真正变化的文档,返回入库报告。"""
    report = {"新增": [], "更新": [], "跳过": []}
    for d in docs:
        text = d["title"] + "。" + d["text"]
        did = doc_id(text)
        if collection.get(ids=[did], include=[])["ids"]:
            report["跳过"].append(d["title"])  # 同 ID 已在库 = 内容一字未变
            continue
        old = collection.get(where={"title": d["title"]}, include=[])
        if old["ids"]:  # 同书名不同哈希 = 修订版:先删旧版再写新版
            collection.delete(ids=old["ids"])
            report["更新"].append(d["title"])
        else:
            report["新增"].append(d["title"])
        vec = embedder.encode([text]).tolist()
        collection.upsert(ids=[did], embeddings=vec, documents=[text],
                          metadatas=[{"title": d["title"], "category": d["category"], "content_hash": did}])
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