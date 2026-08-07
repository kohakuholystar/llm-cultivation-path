"""t60 · s3:MiniBPE 类:编码器与解码器

把 s2 训练出来的合并规则装进一个类,提供 encode(压缩)与
decode(还原)两个方向的能力——这就是一个极简的 tokenizer。
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
    """微型 BPE tokenizer:词表 + 合并规则,提供 encode/decode 双向翻译。"""

    def __init__(self, char_to_id, id_to_char, merges, pieces):
        self.char_to_id = char_to_id
        self.id_to_char = id_to_char
        self.merges = merges
        self.pieces = pieces
        self.base = len(char_to_id)

    @property
    def vocab_size(self):
        """词表大小 = 基础字符数 + 合并规则数。"""
        return self.base + len(self.merges)

    def encode(self, text):
        """把文本压缩成 token id 序列:按训练顺序逐条应用合并规则。"""
        ids = to_char_ids(text, self.char_to_id)
        for idx, (l, r, _cnt) in enumerate(self.merges):
            ids = merge_pair(ids, l, r, self.base + idx)
        return ids

    def decode(self, ids):
        """把 token id 序列还原成文本:用 pieces 查表拼接。"""
        return "".join(self.pieces[i] for i in ids)


def train_mini_bpe(text, num_merges):
    """一条龙训练:清洗 → 建表 → 学合并规则 → 组装 MiniBPE。"""
    clean = clean_text(text)
    char_to_id, id_to_char = build_char_vocab(clean)
    merges, pieces = learn_bpe(clean, num_merges, char_to_id)
    return MiniBPE(char_to_id, id_to_char, merges, pieces)


def main() -> None:
    bpe = train_mini_bpe(CORPUS, 10)
    print(f"词表:基础 {bpe.base} 字符 + {len(bpe.merges)} 条合并 = {bpe.vocab_size} 个 token")
    ids = bpe.encode(CORPUS)
    decoded = bpe.decode(ids)
    print(f"原始 {len(CORPUS)} 字符 → 编码 {len(ids)} 个 token")
    print(f"往返一致: {decoded == CORPUS}")
    print("前 6 条合并规则:")
    for i, (l, r, cnt) in enumerate(bpe.merges[:6], 1):
        piece = bpe.pieces[bpe.base + i - 1]
        print(f"  #{i} 「{bpe.pieces[l]}」+「{bpe.pieces[r]}」 → 「{piece}」(出现 {cnt} 次)")


if __name__ == "__main__":
    main()
