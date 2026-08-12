"""微缩 GPT · s6:温度采样,让模型真正「生成」文字"""


# === 学习契约（面向学生）===
# 本节目标：温度与 top-k 采样:自回归生成。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `text_to_ids(text) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `softmax_for_topk(logits, temperature, top_k) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `generate(model, prompt, length, temperature, top_k, seed) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `TokenEmbedding`：承载本节状态/数据；重点方法：forward。
#   - `SinusoidalPositionalEncoding`：承载本节状态/数据；重点方法：forward。
#   - `ScaledDotProductAttention`：承载本节状态/数据；重点方法：_softmax, forward。
#   - `MultiHeadAttention`：承载本节状态/数据；重点方法：forward。
#   - `LayerNorm`：承载本节状态/数据；重点方法：forward。
#   - `FeedForward`：承载本节状态/数据；重点方法：forward。
#   - `TransformerBlock`：承载本节状态/数据；重点方法：forward。
#   - `TinyGPT`：承载本节状态/数据；重点方法：forward。
# 所属技术栈/模块：模型基础：Tokenizer、numpy、PyTorch、Transformer、训练/微调/量化。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import numpy as np

VOCAB = list("日月星辰山河风雷水火天地方案器运行资源道术")
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
        self.blocks = [TransformerBlock(embed_dim, num_heads, hidden_dim) for _ in range(num_layers)]
        self.norm = LayerNorm(embed_dim)
        self.head = np.random.default_rng(7).normal(0.0, 0.02, (embed_dim, vocab_size))

    def forward(self, ids):
        # TODO: 嵌入与位置编码相加,依次过所有块,返回 x @ self.head 的 logits
        # 提示: x = self.embed.forward(ids) + self.pos_enc.forward(len(ids));for block in self.blocks: x = block.forward(x);return x @ self.head
        raise NotImplementedError("t61-numpy-transformer-s6 尚未实现:请按 TODO 提示实现前向管线")


def softmax_for_topk(logits, temperature, top_k):
    # TODO: 先除以 temperature,再取打分最高的 top_k 个下标,只给保留位算稳定 softmax,其余置 0 并归一化
    # 提示: indices = np.argsort(logits)[-top_k:];scores = logits[indices] - logits[indices].max();probs = np.zeros_like(logits);probs[indices] = np.exp(scores) / np.exp(scores).sum();return probs
    raise NotImplementedError("t61-numpy-transformer-s6 尚未实现:请按 TODO 提示实现 top-k 截断的稳定 softmax")


def generate(model, prompt, length, temperature, top_k, seed):
    # TODO: 用 seed 建 rng,自回归循环 length 次:forward 取 logits[-1] 经 softmax_for_topk 采样,append 进 ids 并拼回字符串
    # 提示: rng = np.random.default_rng(seed);ids = text_to_ids(prompt).tolist();text = prompt;每轮 probs = softmax_for_topk(model.forward(np.asarray(ids))[-1], temperature, top_k),归一化后 next_id = int(rng.choice(len(VOCAB), p=probs)),ids.append(next_id);text += VOCAB[next_id];最后 return text
    raise NotImplementedError("t61-numpy-transformer-s6 尚未实现:请按 TODO 提示实现自回归生成循环")


if __name__ == "__main__":
    ids = text_to_ids("月照山河")
    model = TinyGPT(len(VOCAB), EMBED_DIM, NUM_HEADS, HIDDEN_DIM, NUM_LAYERS)
    print("logits 形状:", model.forward(ids).shape)
    for temp in (0.5, 1.0):
        text = generate(model, "月照山河", 8, temp, top_k=5, seed=42)
        print(f"temperature={temp} → 生成结果: 「{text}」")
