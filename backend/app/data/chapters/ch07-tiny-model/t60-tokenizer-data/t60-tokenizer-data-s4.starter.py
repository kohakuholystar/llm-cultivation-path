"""t60 · s4:数据集构建:滑动窗口样本

GPT 训练要的是 (input, target) 样本对:给定前 8 个 token,预测第 9 个。
本步把 50 个 token 用滑动窗口切成 11 个样本,并校验窗口对齐。
"""
from collections import Counter

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
    """微型 BPE tokenizer:提供 encode 把文本压成 token 序列。"""

    def __init__(self, char_to_id, id_to_char, merges, pieces):
        self.char_to_id = char_to_id
        self.id_to_char = id_to_char
        self.merges = merges
        self.pieces = pieces
        self.base = len(char_to_id)

    def encode(self, text):
        ids = to_char_ids(text, self.char_to_id)
        for idx, (l, r, _cnt) in enumerate(self.merges):
            ids = merge_pair(ids, l, r, self.base + idx)
        return ids


def make_blocks(tokens, block_size, stride):
    """滑动窗口切样本:input 是前 block_size 个 token,target 是错开一位的后续。"""
    blocks = []
    for i in range(0, len(tokens) - block_size, stride):
        # TODO: 用滑动窗口切出 (input, target) 样本对,追加进 blocks
        # 提示: blocks.append((tokens[i:i+block_size], tokens[i+1:i+block_size+1]))
        raise NotImplementedError("t60-tokenizer-data-s4 尚未实现:请按 TODO 提示切出 (input, target) 样本对")
    return blocks


def check_alignment(blocks):
    """校验每个样本:input 去掉首 token 后应等于 target 去掉尾 token。"""
    return all(x[1:] == y[:-1] for x, y in blocks)


def build_dataset(tokens, block_size=8, stride=4):
    """从 token 序列构造 (input, target) 样本集,并返回对齐校验结果。"""
    blocks = make_blocks(tokens, block_size, stride)
    return blocks, check_alignment(blocks)


def main() -> None:
    clean = clean_text(CORPUS)
    char_to_id, id_to_char = build_char_vocab(clean)
    merges, pieces = learn_bpe(clean, 10, char_to_id)
    bpe = MiniBPE(char_to_id, id_to_char, merges, pieces)
    tokens = bpe.encode(clean)
    blocks, ok = build_dataset(tokens, 8, 4)
    print(f"总 token 数: {len(tokens)}")
    print(f"块大小 8,步长 4,滑动窗口得到 {len(blocks)} 个样本")
    print(f"对齐校验: {'全部通过' if ok else '存在错位!'}")
    first = blocks[0]
    print(f"样本 #0: input {first[0]} target {first[1]}")


if __name__ == "__main__":
    main()
