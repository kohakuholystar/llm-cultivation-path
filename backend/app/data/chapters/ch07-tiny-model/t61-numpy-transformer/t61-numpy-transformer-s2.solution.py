"""微缩 GPT · s2:缩放点积注意力

让每个位置「看」其他位置:查询、键、值三分身,Q 与 K 点积
得到注意力分数,除以维度平方根缩放,再经 softmax 归一成权重,
加权求和得上下文向量——这是 Transformer 的心脏。
"""
import numpy as np

VOCAB = list("日月星辰山河风雷水火天地剑器灵气道术")
EMBED_DIM = 32
MAX_SEQ = 16


def char_to_id(ch):
    """把单个字符映射到词表下标;查不到就降级为 0,保证管线不断。"""
    return VOCAB.index(ch) if ch in VOCAB else 0


def text_to_ids(text):
    """把一句文本转成下标序列,最长取前 MAX_SEQ 个字符。"""
    ids = [char_to_id(c) for c in text[:MAX_SEQ]]
    return np.asarray(ids, dtype=np.int64)


class TokenEmbedding:
    """词嵌入层(与 s1 一致):从词表取向量。"""

    def __init__(self, vocab_size, embed_dim):
        rng = np.random.default_rng(0)
        self.weight = rng.normal(0.0, 0.02, (vocab_size, embed_dim))

    def forward(self, ids):
        return self.weight[np.asarray(ids)]


class SinusoidalPositionalEncoding:
    """正弦位置编码(与 s1 一致):偶数维 sin、奇数维 cos。"""

    def __init__(self, max_len, embed_dim):
        pos = np.arange(max_len).reshape(-1, 1)
        dims = np.arange(embed_dim)
        angle = pos / (10000.0 ** (2 * (dims // 2) / embed_dim))
        pe = np.zeros((max_len, embed_dim))
        pe[:, 0::2] = np.sin(angle[:, 0::2])
        pe[:, 1::2] = np.cos(angle[:, 1::2])
        self.pe = pe

    def forward(self, seq_len):
        return self.pe[:seq_len]


class ScaledDotProductAttention:
    """缩放点积注意力:Q·K 点积打分,除以 √dim,softmax 加权 V。"""

    def __init__(self, dim):
        rng = np.random.default_rng(1)
        self.wq = rng.normal(0.0, 0.02, (dim, dim))
        self.wk = rng.normal(0.0, 0.02, (dim, dim))
        self.wv = rng.normal(0.0, 0.02, (dim, dim))

    def _softmax(self, scores):
        # 先减每行最大值,保证指数计算数值稳定
        scores = scores - scores.max(axis=-1, keepdims=True)
        exp = np.exp(scores)
        return exp / exp.sum(axis=-1, keepdims=True)

    def forward(self, x):
        q = x @ self.wq
        k = x @ self.wk
        v = x @ self.wv
        scores = (q @ k.T) / np.sqrt(self.wq.shape[0])
        attn = self._softmax(scores)
        out = attn @ v
        return scores, attn, out


if __name__ == "__main__":
    ids = text_to_ids("月照山河")
    embed = TokenEmbedding(len(VOCAB), EMBED_DIM)
    pos_enc = SinusoidalPositionalEncoding(MAX_SEQ, EMBED_DIM)
    h = embed.forward(ids) + pos_enc.forward(len(ids))
    attn_layer = ScaledDotProductAttention(EMBED_DIM)
    scores, attn, out = attn_layer.forward(h)
    print("scores 形状:", scores.shape)
    print("注意力行和为 1:", np.allclose(attn.sum(axis=-1), 1.0))
    print("out 形状:", out.shape)
