"""藏经阁 · 第 1 步:用 numpy 手写 TF-IDF 嵌入器"""
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


# 藏经阁待数字化的八本秘籍
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


def main():
    embedder = TfidfEmbedder(n=2)
    corpus = [d["title"] + "。" + d["text"] for d in SCRIPTURES]
    embedder.fit(corpus)
    doc_vecs = embedder.encode(corpus)
    print(f"词表大小: {len(embedder.vocab)}  向量维度: {doc_vecs.shape[1]}")

    query = "刚猛的内功心法"
    q_vec = embedder.encode([query])
    sims = (doc_vecs @ q_vec.T).ravel()  # 归一化向量的点积 = 余弦相似度
    print(f"查询: {query}")
    for rank, i in enumerate(np.argsort(-sims)[:3], 1):
        print(f"  TOP{rank} 《{SCRIPTURES[i]['title']}》 相似度 {sims[i]:.4f}")


if __name__ == "__main__":
    main()