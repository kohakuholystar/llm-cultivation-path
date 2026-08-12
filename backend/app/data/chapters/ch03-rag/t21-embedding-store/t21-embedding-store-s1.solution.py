"""黑糖资料室 · 第 1 步:用 numpy 手写 TF-IDF 嵌入器"""
import re

import numpy as np


def char_ngrams(text, n=2):
    """把文本切成字符 n-gram。中文没有天然空格分词,字符二元组是零依赖的稳健切法。"""
    text = re.sub(r"\s+", "", text)
    if len(text) < n:
        return [text]
    return [text[i:i + n] for i in range(len(text) - n + 1)]


class TfidfEmbedder:
    """极简 TF-IDF 嵌入器:fit 建词表,encode 出 L2 归一化向量。

    接口刻意对齐 sentence-transformers 的 encode(),将来换真模型时
    只需替换这一个类,上层入库/检索代码一行不用改。
    """

    def __init__(self, n=2):
        self.n = n
        self.vocab = {}   # token -> 列号
        self.idf = None   # 每个 token 的逆文档频率

    def fit(self, texts):
        df = {}
        for t in texts:
            for tok in set(char_ngrams(t, self.n)):
                df[tok] = df.get(tok, 0) + 1
        tokens = sorted(df)
        self.vocab = {tok: i for i, tok in enumerate(tokens)}
        n_docs = len(texts)
        # 平滑 IDF:log((1+N)/(1+df)) + 1,避免除零也让高频词不为零
        self.idf = np.array([np.log((1 + n_docs) / (1 + df[t])) + 1.0 for t in tokens])
        return self

    def encode(self, texts):
        if self.idf is None:
            raise RuntimeError("请先调用 fit() 构建词表与 IDF")
        mat = np.zeros((len(texts), len(self.vocab)))
        for row, t in enumerate(texts):
            for tok in char_ngrams(t, self.n):
                if tok in self.vocab:  # 未登录词直接忽略
                    mat[row, self.vocab[tok]] += 1.0
        mat *= self.idf  # TF x IDF 加权
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0  # 零向量保护,防止除零
        return mat / norms         # 归一化后,点积即余弦相似度


# 黑糖资料室待数字化的八本参考资料
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
    embedder = TfidfEmbedder(n=2)
    corpus = [d["title"] + "。" + d["text"] for d in SCRIPTURES]
    embedder.fit(corpus)
    doc_vecs = embedder.encode(corpus)
    print(f"词表大小: {len(embedder.vocab)}  向量维度: {doc_vecs.shape[1]}")

    query = "稳定的错误恢复"
    q_vec = embedder.encode([query])
    sims = (doc_vecs @ q_vec.T).ravel()  # 归一化向量的点积 = 余弦相似度
    print(f"查询: {query}")
    for rank, i in enumerate(np.argsort(-sims)[:3], 1):
        print(f"  TOP{rank} 《{SCRIPTURES[i]['title']}》 相似度 {sims[i]:.4f}")


if __name__ == "__main__":
    main()