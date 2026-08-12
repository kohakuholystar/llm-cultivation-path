"""微缩 GPT · s3:多头注意力"""


# === 学习契约（面向学生）===
# 本节目标：多头注意力:并行子空间,一次看见多类关系。完成后能把本节概念放入可运行的工程链路。
# 需要补写：ScaledDotProductAttention；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `text_to_ids(text) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `TokenEmbedding`：承载本节状态/数据；重点方法：forward。
#   - `SinusoidalPositionalEncoding`：承载本节状态/数据；重点方法：forward。
#   - `ScaledDotProductAttention`：承载本节状态/数据；重点方法：_softmax, forward。
#   - `MultiHeadAttention`：承载本节状态/数据；重点方法：forward。
# 所属技术栈/模块：模型基础：Tokenizer、numpy、PyTorch、Transformer、训练/微调/量化。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import numpy as np

VOCAB = list("日月星辰山河风雷水火天地方案器运行资源道术")
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
        # TODO: 创建 num_heads 个 ScaledDotProductAttention(head_dim) 存入 self.heads,再用 rng 初始化输出投影 self.wo,形状 (embed_dim, embed_dim)
        # 提示: self.heads = [ScaledDotProductAttention(head_dim) for _ in range(num_heads)];self.wo = rng.normal(0.0, 0.02, (embed_dim, embed_dim))
        raise NotImplementedError("t61-numpy-transformer-s3 尚未实现:请按 TODO 提示创建多个注意力头并初始化输出投影")

    def forward(self, x):
        # TODO: 按 head_dim 把最后一维切成 num_heads 块,各头分别 forward,沿 axis=-1 拼接后乘 self.wo
        # 提示: chunks = [x[:, i * self.head_dim:(i + 1) * self.head_dim] for i in range(self.num_heads)];heads = np.concatenate([h.forward(c) for h, c in zip(self.heads, chunks)], axis=-1);return heads @ self.wo
        raise NotImplementedError("t61-numpy-transformer-s3 尚未实现:请按 TODO 提示实现多头切块、拼接与投影")


if __name__ == "__main__":
    ids = text_to_ids("月照山河")
    embed = TokenEmbedding(len(VOCAB), EMBED_DIM)
    pos_enc = SinusoidalPositionalEncoding(MAX_SEQ, EMBED_DIM)
    h = embed.forward(ids) + pos_enc.forward(len(ids))
    mha = MultiHeadAttention(EMBED_DIM, NUM_HEADS, HEAD_DIM)
    out = mha.forward(h)
    print("头数:", NUM_HEADS)
    print("多头输出形状:", out.shape)
