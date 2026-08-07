"""t60 · s5:train/val 切分:随机打散与元数据

样本不能全拿去训练——留一小撮当「考官」。本步用固定随机种子
把样本洗牌,按 9:1 切成 train 与 val,并把数据集元数据落盘。
"""
from collections import Counter
import json
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
    blocks = []
    for i in range(0, len(tokens) - block_size, stride):
        blocks.append((tokens[i:i + block_size], tokens[i + 1:i + block_size + 1]))
    return blocks


def split_dataset(blocks, ratio=0.9, seed=42):
    """固定种子洗牌,按 ratio 切成 (train, val) 两段。"""
    shuffled = list(blocks)
    random.Random(seed).shuffle(shuffled)
    n_train = int(len(shuffled) * ratio)
    # TODO: 按 n_train 用切片把 shuffled 切成 (train, val) 两段并返回
    # 提示: train 取前 n_train 个,val 取剩下的:shuffled[:n_train] / shuffled[n_train:]
    raise NotImplementedError("t60-tokenizer-data-s5 尚未实现:请按 TODO 提示用切片切出 train/val 两段")


def save_metadata(path, meta):
    """把数据集元数据写成 JSON 文件。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def main() -> None:
    clean = clean_text(CORPUS)
    char_to_id, id_to_char = build_char_vocab(clean)
    merges, pieces = learn_bpe(clean, 10, char_to_id)
    bpe = MiniBPE(char_to_id, id_to_char, merges, pieces)
    tokens = bpe.encode(clean)
    blocks = make_blocks(tokens, 8, 4)
    train, val = split_dataset(blocks)
    print("== train/val 切分 ==")
    print(f"  train: {len(train)} 个样本")
    print(f"  val: {len(val)} 个样本")
    print(f"  切分前后样本总数一致: {len(train) + len(val) == len(blocks)}")
    meta = {
        "vocab_size": len(bpe.char_to_id) + len(bpe.merges),
        "num_merges": len(bpe.merges),
        "n_tokens": len(tokens),
        "n_blocks": len(blocks),
        "n_train": len(train),
        "n_val": len(val),
    }
    save_metadata("tiny_dataset_meta.json", meta)
    print("元数据已写入 tiny_dataset_meta.json")
    with open("tiny_dataset_meta.json", encoding="utf-8") as f:
        back = json.load(f)
    print(f"回读元数据: vocab_size={back['vocab_size']}, n_train={back['n_train']}, n_val={back['n_val']}")


if __name__ == "__main__":
    main()
