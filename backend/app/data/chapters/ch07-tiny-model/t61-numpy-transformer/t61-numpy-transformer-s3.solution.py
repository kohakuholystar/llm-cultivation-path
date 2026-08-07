"""微缩 GPT · s3:多头注意力"""
import numpy as np

VOCAB = list("日月星辰山河风雷水火天地剑器灵气道术")
EMBED_DIM = 32
MAX_SEQ = 16
NUM_HEADS = 4
HEAD_DIM = 8


def text_to_ids(text):
    return np.asarray([VOCAB.index(c) if c in VOCAB else 0 for c in text[:MAX_SEQ]], dtype=np.int64)


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
    """单头缩放点积注意力:Q/K/V 投影,缩放点积,softmax,加权求和。"""

    def __init__(self, dim):
        rng = np.random.default_rng(1)
        self.wq = rng.normal(0.0, 0.02, (dim, dim))
        self.wk = rng.normal(0.0, 0.02, (dim, dim))
        self.wv = rng.normal(0.0, 0.02, (dim, dim))

    def _softmax(self, scores):
        scores = scores - scores.max(axis=-1, keepdims=True)
        exp = np.exp(scores)
        return exp / exp.sum(axis=-1, keepdims=True)

    def forward(self, x):
        q = x @ self.wq
        k = x @ self.wk
        v = x @ self.wv
        scores = (q @ k.T) / np.sqrt(self.wq.shape[0])
        attn = self._softmax(scores)
        return attn @ v


class MultiHeadAttention:
    """多头注意力:多个头并行看不同子空间,拼接后线性投影融合。"""

    def __init__(self, embed_dim, num_heads, head_dim):
        rng = np.random.default_rng(2)
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.heads = [ScaledDotProductAttention(head_dim) for _ in range(num_heads)]
        self.wo = rng.normal(0.0, 0.02, (embed_dim, embed_dim))

    def forward(self, x):
        chunks = [x[:, i * self.head_dim:(i + 1) * self.head_dim] for i in range(self.num_heads)]
        heads = np.concatenate([h.forward(c) for h, c in zip(self.heads, chunks)], axis=-1)
        return heads @ self.wo


if __name__ == "__main__":
    ids = text_to_ids("月照山河")
    embed = TokenEmbedding(len(VOCAB), EMBED_DIM)
    pos_enc = SinusoidalPositionalEncoding(MAX_SEQ, EMBED_DIM)
    h = embed.forward(ids) + pos_enc.forward(len(ids))
    mha = MultiHeadAttention(EMBED_DIM, NUM_HEADS, HEAD_DIM)
    out = mha.forward(h)
    print("头数:", NUM_HEADS)
    print("多头输出形状:", out.shape)
