"""微缩 GPT · s4:LayerNorm、前馈网络与完整 Transformer 块"""
import numpy as np

VOCAB = list("日月星辰山河风雷水火天地方案器运行资源道术")
EMBED_DIM = 32
MAX_SEQ = 16
NUM_HEADS = 4
HIDDEN_DIM = 64


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
    """单头注意力:缩放点积 + softmax + 加权求和。"""

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
    """多头注意力:切块并行,拼接后投影(头维度自动推导)。"""

    def __init__(self, embed_dim, num_heads):
        head_dim = embed_dim // num_heads
        rng = np.random.default_rng(2)
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.heads = [ScaledDotProductAttention(head_dim) for _ in range(num_heads)]
        self.wo = rng.normal(0.0, 0.02, (embed_dim, embed_dim))

    def forward(self, x):
        chunks = [x[:, i * self.head_dim:(i + 1) * self.head_dim] for i in range(self.num_heads)]
        heads = np.concatenate([h.forward(c) for h, c in zip(self.heads, chunks)], axis=-1)
        return heads @ self.wo


class LayerNorm:
    """层归一化:按最后一维标准化,再缩放平移,稳定训练。"""

    def __init__(self, dim):
        rng = np.random.default_rng(3)
        self.gamma = rng.normal(0.0, 0.02, (dim,))
        self.beta = rng.normal(0.0, 0.02, (dim,))

    def forward(self, x):
        mean = x.mean(axis=-1, keepdims=True)
        var = x.var(axis=-1, keepdims=True)
        return (x - mean) / np.sqrt(var + 1e-5) * self.gamma + self.beta


class FeedForward:
    """前馈网络:升维 → ReLU → 降维,给模型非线性。"""

    def __init__(self, embed_dim, hidden_dim):
        rng = np.random.default_rng(4)
        self.w1 = rng.normal(0.0, 0.02, (embed_dim, hidden_dim))
        self.b1 = rng.normal(0.0, 0.02, (hidden_dim,))
        self.w2 = rng.normal(0.0, 0.02, (hidden_dim, embed_dim))
        self.b2 = rng.normal(0.0, 0.02, (embed_dim,))

    def forward(self, x):
        return np.maximum(x @ self.w1 + self.b1, 0.0) @ self.w2 + self.b2


class TransformerBlock:
    """Transformer 块:Pre-LN 的注意力 + 前馈,各带残差。"""

    def __init__(self, embed_dim, num_heads, hidden_dim):
        self.attn = MultiHeadAttention(embed_dim, num_heads)
        self.ffn = FeedForward(embed_dim, hidden_dim)
        self.norm1 = LayerNorm(embed_dim)
        self.norm2 = LayerNorm(embed_dim)

    def forward(self, x):
        x = x + self.attn.forward(self.norm1.forward(x))
        x = x + self.ffn.forward(self.norm2.forward(x))
        return x


if __name__ == "__main__":
    ids = text_to_ids("月照山河")
    embed = TokenEmbedding(len(VOCAB), EMBED_DIM)
    pos_enc = SinusoidalPositionalEncoding(MAX_SEQ, EMBED_DIM)
    h = embed.forward(ids) + pos_enc.forward(len(ids))
    block = TransformerBlock(EMBED_DIM, NUM_HEADS, HIDDEN_DIM)
    out = block.forward(h)
    print("块输出形状:", out.shape)
    print("输出均值:", f"{out.mean():.4f}")
