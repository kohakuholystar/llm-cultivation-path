"""微缩 GPT · s5:组装 TinyGPT,输出 logits,预测下一个字"""
import numpy as np

VOCAB = list("日月星辰山河风雷水火天地剑器灵气道术")
EMBED_DIM = 32
MAX_SEQ = 16
NUM_HEADS = 4
HIDDEN_DIM = 64
NUM_LAYERS = 2


def text_to_ids(text):
    return np.asarray([VOCAB.index(c) if c in VOCAB else 0 for c in text[:MAX_SEQ]], dtype=np.int64)


class TokenEmbedding:
    def __init__(self, vocab_size, embed_dim):
        rng = np.random.default_rng(0)
        self.weight = rng.normal(0.0, 0.02, (vocab_size, embed_dim))

    def forward(self, ids):
        return self.weight[np.asarray(ids)]


class SinusoidalPositionalEncoding:
    def __init__(self, max_len, embed_dim):
        div = np.exp(np.arange(0, embed_dim, 2) * (-np.log(10000.0) / embed_dim))
        pos = np.arange(max_len)[:, None]
        pe = np.zeros((max_len, embed_dim))
        pe[:, 0::2] = np.sin(pos * div)
        pe[:, 1::2] = np.cos(pos * div)
        self.pe = pe

    def forward(self, seq_len):
        return self.pe[:seq_len]


class ScaledDotProductAttention:
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
    def __init__(self, dim):
        rng = np.random.default_rng(3)
        self.gamma = rng.normal(0.0, 0.02, (dim,))
        self.beta = rng.normal(0.0, 0.02, (dim,))

    def forward(self, x):
        mean = x.mean(axis=-1, keepdims=True)
        var = x.var(axis=-1, keepdims=True)
        return (x - mean) / np.sqrt(var + 1e-5) * self.gamma + self.beta


class FeedForward:
    def __init__(self, embed_dim, hidden_dim):
        rng = np.random.default_rng(4)
        self.w1 = rng.normal(0.0, 0.02, (embed_dim, hidden_dim))
        self.b1 = rng.normal(0.0, 0.02, (hidden_dim,))
        self.w2 = rng.normal(0.0, 0.02, (hidden_dim, embed_dim))
        self.b2 = rng.normal(0.0, 0.02, (embed_dim,))

    def forward(self, x):
        return np.maximum(x @ self.w1 + self.b1, 0.0) @ self.w2 + self.b2


class TransformerBlock:
    def __init__(self, embed_dim, num_heads, hidden_dim):
        self.attn = MultiHeadAttention(embed_dim, num_heads)
        self.ffn = FeedForward(embed_dim, hidden_dim)
        self.norm1 = LayerNorm(embed_dim)
        self.norm2 = LayerNorm(embed_dim)

    def forward(self, x):
        x = x + self.attn.forward(self.norm1.forward(x))
        x = x + self.ffn.forward(self.norm2.forward(x))
        return x


class TinyGPT:
    """微缩 GPT:嵌入 + 位置编码 + 两层 Transformer 块 + 输出头。"""

    def __init__(self, vocab_size, embed_dim, num_heads, hidden_dim, num_layers):
        self.embed = TokenEmbedding(vocab_size, embed_dim)
        self.pos_enc = SinusoidalPositionalEncoding(MAX_SEQ, embed_dim)
        # TODO: 创建 num_layers 个 TransformerBlock(embed_dim, num_heads, hidden_dim) 存入 self.blocks,再建顶层 self.norm 与输出头 self.head(embed_dim × vocab_size,default_rng(7) 初始化)
        # 提示: self.blocks = [TransformerBlock(embed_dim, num_heads, hidden_dim) for _ in range(num_layers)];self.norm = LayerNorm(embed_dim);self.head = np.random.default_rng(7).normal(0.0, 0.02, (embed_dim, vocab_size))
        raise NotImplementedError("t61-numpy-transformer-s5 尚未实现:请按 TODO 提示装配 TinyGPT 的块、顶层归一化与输出头")

    def forward(self, ids):
        # TODO: 嵌入与位置编码相加,依次过所有块,最后返回 x @ self.head 的 logits
        # 提示: x = self.embed.forward(ids) + self.pos_enc.forward(len(ids));for block in self.blocks: x = block.forward(x);return x @ self.head
        raise NotImplementedError("t61-numpy-transformer-s5 尚未实现:请按 TODO 提示实现前向管线")

    def predict(self, ids):
        # TODO: 取 logits[-1],先减最大值再 exp 归一化,argmax 得下标,返回下标与对应概率
        # 提示: logits = self.forward(ids)[-1];exp = np.exp(logits - logits.max());probs = exp / exp.sum();idx = int(np.argmax(probs));return idx, float(probs[idx])
        raise NotImplementedError("t61-numpy-transformer-s5 尚未实现:请按 TODO 提示实现下一个字预测")


if __name__ == "__main__":
    ids = text_to_ids("月照山河")
    model = TinyGPT(len(VOCAB), EMBED_DIM, NUM_HEADS, HIDDEN_DIM, NUM_LAYERS)
    print("logits 形状:", model.forward(ids).shape)
    idx, prob = model.predict(ids)
    print(f"预测下标 {idx},概率 {prob:.3f},预测下一个字「{VOCAB[idx]}」")
