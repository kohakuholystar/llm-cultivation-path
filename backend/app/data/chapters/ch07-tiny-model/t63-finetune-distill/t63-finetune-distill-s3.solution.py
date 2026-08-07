"""袖里乾坤 · s3:微调教材——语料、编码与交叉熵

要让小模型「学会说话」,先备好教材:把语料切成
「前一个字 → 后一个字」的配对,把字转成编号,再用
交叉熵度量预测分布与真实下一个字的差距。交叉熵越小,
模型越懂语料的规律。
"""
import numpy as np

CORPUS = ("乾坤炉中炼真火,火候三分见丹青。"
          "丹青入册藏经阁,阁中坐忘修心性。"
          "心性圆融通大道,大道无形育众生。")
chars = sorted(set(CORPUS))
VOCAB = len(chars)
CHAR_IDS = {c: i for i, c in enumerate(chars)}
IDS = np.array([CHAR_IDS[c] for c in CORPUS], dtype=np.int64)


def encode(text: str) -> np.ndarray:
    """把一句话转成编号数组。"""
    return np.array([CHAR_IDS[c] for c in text], dtype=np.int64)


def decode(ids) -> str:
    """把编号数组还原成一句话。"""
    return "".join(chars[int(i)] for i in ids)


def build_bigram_data(ids):
    """构造 bigram 数据:输入前一字,预测后一字。"""
    return ids[:-1], ids[1:]


def to_onehot(xs, vocab: int) -> np.ndarray:
    """编号 → one-hot 矩阵(每行一个样本)。"""
    x = np.zeros((len(xs), vocab), dtype=np.float64)
    x[np.arange(len(xs)), xs] = 1.0
    return x


def softmax(z):
    """按行 softmax,先减行最大值防止溢出。"""
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def cross_entropy_with_grad(logits, ys):
    """交叉熵损失与其对 logits 的梯度。

    梯度有个优雅的封闭形式:(softmax(logits) - onehot(ys)) / n,
    直接以解析式返回,后续 SGD 全靠它。
    """
    p = softmax(logits)
    n = logits.shape[0]
    loss = float(-np.mean(np.log(p[np.arange(n), ys] + 1e-12)))
    d = (p - np.eye(logits.shape[1])[ys]) / n
    return loss, d


def main() -> None:
    print("== 微调教材:语料、编码与交叉熵 ==")
    print(f"语料 {len(CORPUS)} 字 | 词表 {VOCAB} 字 | 样本 {len(IDS) - 1} 条")
    print("字表:", " ".join(chars))

    xs, ys = build_bigram_data(IDS)
    x = to_onehot(xs, VOCAB)
    print(f"样例:『{decode(IDS[:3])}』→『{decode(IDS[1:4])}』(前两字预测第三字)")

    # 随机初始化的模型没有学习,loss 应与 ln(VOCAB) 同量级
    rng = np.random.default_rng(42)
    w = rng.normal(0.0, 0.3, size=(VOCAB, VOCAB))
    loss, _ = cross_entropy_with_grad(x @ w, ys)
    print(f"随机初始 loss = {loss:.4f}(ln{VOCAB} ≈ {np.log(VOCAB):.4f})")

    p = softmax(x @ w)
    top = np.argsort(p[0])[::-1][:5]
    print(f"首字『{decode(IDS[0:1])}』的 top5 预测:",
          " ".join(decode([t]) for t in top))
    print("交叉熵越小,预测分布越贴近真实的下一字")


if __name__ == "__main__":
    main()
