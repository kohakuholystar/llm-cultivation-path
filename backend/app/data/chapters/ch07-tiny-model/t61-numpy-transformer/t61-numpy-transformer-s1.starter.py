"""微缩 GPT · s1:词表、词嵌入与正弦位置编码

从零搭建迷你 GPT,先打好地基:字符词表、可训练词嵌入层,
以及给每个位置打上「坐标」的正弦位置编码。矩阵形状
(seq_len, embed_dim) 是后面所有层的通用语言。
"""


# === 学习契约（面向学生）===
# 本节目标：词表与词嵌入:给字符编码,再打上位置坐标。完成后能把本节概念放入可运行的工程链路。
# 需要补写：default_rng；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `char_to_id(ch) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：把单个字符映射到词表下标;查不到就降级为 0,保证管线不断。
#   - `text_to_ids(text) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：把一句文本转成下标序列,最长取前 MAX_SEQ 个字符。
#   - `TokenEmbedding`：承载本节状态/数据；重点方法：forward。
#   - `SinusoidalPositionalEncoding`：承载本节状态/数据；重点方法：forward。
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
    """可训练词嵌入表:每个词一个可学习向量,形状 (vocab_size, embed_dim)。"""

    def __init__(self, vocab_size, embed_dim):
        # TODO: 用 np.random.default_rng(0) 固定随机种子,再用 rng.normal(0.0, 0.02, (vocab_size, embed_dim)) 初始化 self.weight
        # 提示: rng = np.random.default_rng(0);self.weight = rng.normal(0.0, 0.02, (vocab_size, embed_dim))
        raise NotImplementedError("t61-numpy-transformer-s1 尚未实现:请按 TODO 提示初始化词嵌入权重")

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
        # TODO: 用 np.zeros 准备 (max_len, embed_dim) 的位置矩阵,偶数维填 np.sin、奇数维填 np.cos,存入 self.pe
        # 提示: pe = np.zeros((max_len, embed_dim));pe[:, 0::2] = np.sin(angle[:, 0::2]);pe[:, 1::2] = np.cos(angle[:, 1::2]);self.pe = pe
        raise NotImplementedError("t61-numpy-transformer-s1 尚未实现:请按 TODO 提示填充正弦位置编码矩阵")

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
