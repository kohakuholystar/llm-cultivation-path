"""黑糖资料室 · 第 6 步:封装 ScriptureStore —— 一个可复用的向量入库组件"""
# 学习契约
# 目标：完成 t21-embedding-store-s6 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 6 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：char_ngrams(text, n) -> 未标注; doc_id(text) -> 未标注; main() -> 未标注。
# 技术栈：re, hashlib, numpy, chromadb。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
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
    """黑糖资料室向量库:建索引、增量同步、语义检索一站封装(替换点:Client 与 Embedder)。"""

    def __init__(self, name="cangjingge", ngram=2):
        self.collection = chromadb.EphemeralClient().get_or_create_collection(
            name, metadata={"hnsw:space": "cosine"})
        self.embedder = TfidfEmbedder(n=ngram)

    @staticmethod
    def _full_text(d):
        return d["title"] + "。" + d["text"]

    def build_index(self, docs, batch_size=4):
        """首次建库:fit 词表,然后分批 upsert,返回总条数。"""
        # TODO: 用 self._full_text 取文本列表,fit 词表后全量 encode,再按 batch_size 分批 upsert。
        # 提示: texts = [self._full_text(d) for d in docs];vecs = self.embedder.encode(texts).tolist()
        #       for start in range(0, len(docs), batch_size):
        #         batch = docs[start:start + batch_size]
        #         self.collection.upsert(ids=[doc_id(self._full_text(d)) for d in batch],
        #                                embeddings=vecs[start:start + batch_size],
        #                                documents=texts[start:start + batch_size],
        #                                metadatas=[{"title": d["title"], "category": d["category"]} for d in batch])
        #       return self.collection.count()
        raise NotImplementedError("t21-embedding-store-s6 尚未实现:请按 TODO 提示补全 build_index")

    def sync(self, docs):
        """增量同步:哈希去重,修订版先删后写,返回入库报告。"""
        report = {"新增": 0, "更新": 0, "跳过": 0}
        # TODO: 逐条三态判定:同 ID 跳过;同书名不同哈希 = 修订版,先删旧版再 upsert 记"更新";否则 upsert 记"新增"。
        # 提示: if self.collection.get(ids=[did], include=[])["ids"]: report["跳过"] += 1; continue
        #       old = self.collection.get(where={"title": d["title"]}, include=[])
        #       if old["ids"]: self.collection.delete(ids=old["ids"]); report["更新"] += 1
        #       else: report["新增"] += 1
        #       self.collection.upsert(ids=[did], embeddings=self.embedder.encode([text]).tolist(),
        #                              documents=[text], metadatas=[{"title": d["title"], "category": d["category"]}])
        raise NotImplementedError("t21-embedding-store-s6 尚未实现:请按 TODO 提示补全 sync 三态判定")
        return report

    def search(self, query, top_k=3, category=None):
        """语义检索:查询向量化 -> Top-K -> 余弦距离换算成相似度。"""
        # TODO: 复用第 5 步的检索三部曲并组装结果。
        # 提示: result = self.collection.query(
        #         query_embeddings=self.embedder.encode([query]).tolist(),
        #         n_results=top_k, where={"category": category} if category else None,
        #         include=["metadatas", "distances"])
        #       return [{"title": m["title"], "score": round(1.0 - dist, 4)}
        #               for m, dist in zip(result["metadatas"][0], result["distances"][0])]
        raise NotImplementedError("t21-embedding-store-s6 尚未实现:请按 TODO 提示补全 search 检索")


def main():
    scriptures = [
        {"title": "检索基础指南", "category": "基础指南", "text": "输入表达可以变化，核心语义应保持稳定。索引构建完成后，应使用固定查询集验证召回结果。"},
        {"title": "数据清洗手册", "category": "基础指南", "text": "清理冗余信息，补足缺失字段，并统一编码、日期与枚举值。"},
        {"title": "重排设计指南", "category": "检索工程", "text": "减少无效规则，优先识别相关信号，并使用稳定排序避免结果漂移。"},
        {"title": "引用规范", "category": "检索工程", "text": "回答中的事实必须标注来源编号，且编号能够回到原始文档。"},
        {"title": "故障恢复指南", "category": "运行保障", "text": "服务异常时先记录错误，再按重试、降级与状态恢复顺序处理。"},
        {"title": "文档切分指南", "category": "检索工程", "text": "按标题、段落与长度边界切分文档，并保留必要的上下文重叠。"},
    ]
    store = ScriptureStore()
    print(f"建库完成: {store.build_index(scriptures)} 条操作指南")
    updates = [scriptures[0], {"title": "神照经", "category": "基础指南", "text": "神照功处理能力浑厚，有起死回生之效"}]  # 1 重复 1 新增
    print(f"增量同步报告: {store.sync(updates)}")
    for i, h in enumerate(store.search("稳定的技术方案", top_k=2), 1):
        print(f"  TOP{i} 《{h['title']}》 相似度 {h['score']}")


if __name__ == "__main__":
    main()
