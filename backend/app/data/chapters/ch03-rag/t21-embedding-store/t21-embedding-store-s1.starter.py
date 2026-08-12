"""黑糖资料室 · 第 1 步:用 numpy 手写 TF-IDF 嵌入器"""
# 学习契约
# 目标：完成 t21-embedding-store-s1 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 4 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：char_ngrams(text, n) -> 未标注; main() -> 未标注。
# 技术栈：re, numpy。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
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
        # TODO: 完成 TF x IDF 加权与 L2 归一化,返回归一化矩阵。
        # 提示: mat *= self.idf;用 np.linalg.norm(mat, axis=1, keepdims=True) 求每行范数,
        #       0 范数先替换为 1.0 防除零,最后 return mat / norms
        raise NotImplementedError("t21-embedding-store-s1 尚未实现:请按 TODO 提示完成 TF×IDF 加权与 L2 归一化")


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
    # TODO: 计算每篇文档与查询的余弦相似度并打印 TOP3。
    # 提示:归一化向量的点积即余弦相似度 -> sims = (doc_vecs @ q_vec.T).ravel(),
    #       用 np.argsort(-sims) 取降序下标
    raise NotImplementedError("t21-embedding-store-s1 尚未实现:请按 TODO 提示计算并打印相似度 TOP3")


if __name__ == "__main__":
    main()
