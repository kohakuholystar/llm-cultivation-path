"""t60 · s6:总装一条龙:微型 GPT 数据管道

把 s1-s5 的所有环节接成一条流水线:清洗 → 训练 BPE → 编码 →
切块 → 切分 → 自检,一口气得到微型 GPT 的完整训练数据。
"""


# === 学习契约（面向学生）===
# 本节目标：总装一条龙:微型 GPT 数据管道。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `clean_text(text) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `build_char_vocab(text) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `to_char_ids(text, char_to_id) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `most_frequent_pair(ids) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `merge_pair(ids, left, right, new_id) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `learn_bpe(text, num_merges, char_to_id) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `make_blocks(tokens, block_size, stride) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `split_dataset(blocks, ratio=0.9, seed=42) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `build_pipeline(text, num_merges=10, block_size=8, stride=4, ratio=0.9, seed=42) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：一条龙:清洗 → 训练 BPE → 编码 → 切块 → 切分,返回完整数据管道。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `MiniBPE`：承载本节状态/数据；重点方法：vocab_size, encode, decode。
# 所属技术栈/模块：模型基础：Tokenizer、numpy、PyTorch、Transformer、训练/微调/量化。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
from collections import Counter
import random

CORPUS = (
    "床前明月光,疑是地上霜。举头望明月,低头思故乡。"
    "床前明月光,疑是地上霜。举头望明月,低头思故乡。"
    "白日依山尽,黄河入海流。欲穷千里目,更上一层楼。"
)


def clean_text(text):
    text = text.replace("\u3000", "")
    return "".join(ch for ch in text if ch.isprintable())


def build_char_vocab(text):
    chars = sorted(set(text))
    char_to_id = {ch: i for i, ch in enumerate(chars)}
    id_to_char = {i: ch for ch, i in char_to_id.items()}
    return char_to_id, id_to_char


def to_char_ids(text, char_to_id):
    return [char_to_id[ch] for ch in text]


def most_frequent_pair(ids):
    pairs = Counter(zip(ids, ids[1:]))
    if not pairs:
        return (-1, -1), 0
    return pairs.most_common(1)[0]


def merge_pair(ids, left, right, new_id):
    merged = []
    i = 0
    while i < len(ids):
        if i + 1 < len(ids) and ids[i] == left and ids[i + 1] == right:
            merged.append(new_id)
            i += 2
        else:
            merged.append(ids[i])
            i += 1
    return merged


def learn_bpe(text, num_merges, char_to_id):
    ids = to_char_ids(text, char_to_id)
    pieces = {i: ch for ch, i in char_to_id.items()}
    merges = []
    base = len(char_to_id)
    for idx in range(num_merges):
        (l, r), cnt = most_frequent_pair(ids)
        if cnt < 2:
            break
        merges.append((l, r, cnt))
        pieces[base + idx] = pieces[l] + pieces[r]
        ids = merge_pair(ids, l, r, base + idx)
    return merges, pieces


class MiniBPE:
    """微型 BPE tokenizer:encode 压缩、decode 还原。"""

    def __init__(self, char_to_id, id_to_char, merges, pieces):
        self.char_to_id = char_to_id
        self.id_to_char = id_to_char
        self.merges = merges
        self.pieces = pieces
        self.base = len(char_to_id)

    @property
    def vocab_size(self):
        return self.base + len(self.merges)

    def encode(self, text):
        ids = to_char_ids(text, self.char_to_id)
        for idx, (l, r, _cnt) in enumerate(self.merges):
            ids = merge_pair(ids, l, r, self.base + idx)
        return ids

    def decode(self, ids):
        return "".join(self.pieces[i] for i in ids)


def make_blocks(tokens, block_size, stride):
    blocks = []
    for i in range(0, len(tokens) - block_size, stride):
        blocks.append((tokens[i:i + block_size], tokens[i + 1:i + block_size + 1]))
    return blocks


def split_dataset(blocks, ratio=0.9, seed=42):
    shuffled = list(blocks)
    random.Random(seed).shuffle(shuffled)
    n_train = int(len(shuffled) * ratio)
    train, val = shuffled[:n_train], shuffled[n_train:]
    return train, val


def build_pipeline(text, num_merges=10, block_size=8, stride=4, ratio=0.9, seed=42):
    """一条龙:清洗 → 训练 BPE → 编码 → 切块 → 切分,返回完整数据管道。"""
    # TODO: 依次调用 clean_text / build_char_vocab / learn_bpe / MiniBPE /
    #       make_blocks / split_dataset,组装 bpe、tokens、blocks、train、val、stats
    # 提示: clean_text(text) → build_char_vocab(clean) → learn_bpe(clean, num_merges, char_to_id)
    #       → MiniBPE(char_to_id, id_to_char, merges, pieces) → bpe.encode(clean)
    #       → make_blocks(tokens, block_size, stride) → split_dataset(blocks, ratio, seed);
    #       stats 汇总 chars/vocab_size/num_merges/n_tokens/n_blocks/n_train/n_val
    raise NotImplementedError("t60-tokenizer-data-s6 尚未实现:请按 TODO 提示串联整条数据管道并组装返回字典")
    return {"bpe": bpe, "tokens": tokens, "blocks": blocks,
            "train": train, "val": val, "stats": stats}


def main() -> None:
    pipe = build_pipeline(CORPUS)
    s = pipe["stats"]
    print(f"词表:基础 {s['vocab_size'] - s['num_merges']} 字符 + {s['num_merges']} 条合并 = {s['vocab_size']} token")
    print(f"编码: {s['chars']} 字符 → {s['n_tokens']} token → {s['n_blocks']} 个样本")
    print(f"切分: train {s['n_train']} / val {s['n_val']}")
    print("== 出厂自检 ==")
    print(f"  往返一致: {pipe['bpe'].decode(pipe['bpe'].encode(CORPUS)) == CORPUS}")
    print(f"  窗口对齐: {all(x[1:] == y[:-1] for x, y in pipe['blocks'])}")
    print(f"  切分互斥: {not any(tb in pipe['train'] for tb in pipe['val'])}")


if __name__ == "__main__":
    main()
