"""微缩 GPT · s1:词表、词嵌入与正弦位置编码

从零搭建迷你 GPT,先打好地基:字符词表、可训练词嵌入层,
以及给每个位置打上「坐标」的正弦位置编码。矩阵形状
(seq_len, embed_dim) 是后面所有层的通用语言。
"""
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
    """可训练词嵌入表:每个词一个可学习向量,形状 (vocab_size, embed_dim)。"""

    def __init__(self, vocab_size, embed_dim):
        # 固定随机种子,保证每次运行结果一致
        rng = np.random.default_rng(0)
        # 用 0.02 的小标准差初始化,让向量远离饱和区
        self.weight = rng.normal(0.0, 0.02, (vocab_size, embed_dim))

    def forward(self, ids):
        # 查表:下标数组去 weight 里取行,得到 (seq_len, embed_dim)
        return self.weight[np.asarray(ids)]


class SinusoidalPositionalEncoding:
    """正弦位置编码:偶数维用 sin、奇数维用 cos,位置之间可区分。"""

    def __init__(self, max_len, embed_dim):
        pos = np.arange(max_len).reshape(-1, 1)
        dims = np.arange(embed_dim)
        # 不同维度波长不同:低频编码远距离,高频编码近距离
        angle = pos / (10000.0 ** (2 * (dims // 2) / embed_dim))
        pe = np.zeros((max_len, embed_dim))
        # 偶数维填 sin,奇数维填 cos,拼出独一无二的位置坐标
        pe[:, 0::2] = np.sin(angle[:, 0::2])
        pe[:, 1::2] = np.cos(angle[:, 1::2])
        self.pe = pe

    def forward(self, seq_len):
        return self.pe[:seq_len]


if __name__ == "__main__":
    ids = text_to_ids("月照山河")
    print("词表大小:", len(VOCAB))
    print("输入下标:", ids.tolist())
    print("输入序列长度:", len(ids))
    embed = TokenEmbedding(len(VOCAB), EMBED_DIM)
    pos_enc = SinusoidalPositionalEncoding(MAX_SEQ, EMBED_DIM)
    # 词嵌入 + 位置编码 = 带位置信息的输入向量
    x = embed.forward(ids)
    h = x + pos_enc.forward(len(ids))
    print("词嵌入 x 形状:", x.shape)
    print("位置编码 pe 形状:", pos_enc.forward(len(ids)).shape)
    print("相加后 h 形状:", h.shape)
