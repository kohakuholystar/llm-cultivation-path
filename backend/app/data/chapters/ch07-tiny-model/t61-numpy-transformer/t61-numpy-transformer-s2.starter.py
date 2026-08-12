"""微缩 GPT · s2:缩放点积注意力

让每个位置「看」其他位置:查询、键、值三分身,Q 与 K 点积
得到注意力分数,除以维度平方根缩放,再经 softmax 归一成权重,
加权求和得上下文向量——这是 Transformer 的心脏。
"""


# === 学习契约（面向学生）===
# 本节目标：缩放点积注意力:让每个位置看见其他位置。完成后能把本节概念放入可运行的工程链路。
# 需要补写：default_rng；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `char_to_id(ch) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：把单个字符映射到词表下标;查不到就降级为 0,保证管线不断。
#   - `text_to_ids(text) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：把一句文本转成下标序列,最长取前 MAX_SEQ 个字符。
#   - `TokenEmbedding`：承载本节状态/数据；重点方法：forward。
#   - `SinusoidalPositionalEncoding`：承载本节状态/数据；重点方法：forward。
#   - `ScaledDotProductAttention`：承载本节状态/数据；重点方法：_softmax, forward。
# 所属技术栈/模块：模型基础：Tokenizer、numpy、PyTorch、Transformer、训练/微调/量化。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import numpy as np

VOCAB = list("日月星辰山河风雷水火天地方案器运行资源道术")
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
        # TODO: 用 np.random.default_rng(1) 创建随机源,初始化 self.wq / self.wk / self.wv 三个 (dim, dim) 投影矩阵
        # 提示: rng = np.random.default_rng(1);self.wq = rng.normal(0.0, 0.02, (dim, dim))(self.wk / self.wv 同理)
        raise NotImplementedError("t61-numpy-transformer-s2 尚未实现:请按 TODO 提示初始化 Q/K/V 三个投影矩阵")

    def _softmax(self, scores):
        # TODO: 先减每行最大值保证数值稳定,再求 exp 并按行归一化,返回概率矩阵
        # 提示: scores = scores - scores.max(axis=-1, keepdims=True);exp = np.exp(scores);return exp / exp.sum(axis=-1, keepdims=True)
        raise NotImplementedError("t61-numpy-transformer-s2 尚未实现:请按 TODO 提示实现数值稳定的 softmax")

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
