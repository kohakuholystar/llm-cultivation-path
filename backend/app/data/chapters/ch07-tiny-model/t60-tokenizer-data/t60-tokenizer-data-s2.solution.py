"""t60 · s2:BPE 合并规则:从高频字对开始

词表只有 38 个字符时,「床前明月光」要拆成 5 个 token,太啰嗦。
本步实现 BPE(Byte Pair Encoding)的核心:反复统计相邻 token 对,
把出现次数最高的字对合并成一个新 token,循环 num_merges 次。
"""
from collections import Counter

CORPUS = (
    "床前明月光,疑是地上霜。举头望明月,低头思故乡。"
    "床前明月光,疑是地上霜。举头望明月,低头思故乡。"
    "白日依山尽,黄河入海流。欲穷千里目,更上一层楼。"
)


def clean_text(text):
    """清洗语料:剔除全角空格与不可打印字符。"""
    text = text.replace("\u3000", "")
    return "".join(ch for ch in text if ch.isprintable())


def build_char_vocab(text):
    """按字典序建立 char_to_id 与 id_to_char 双向映射。"""
    chars = sorted(set(text))
    char_to_id = {ch: i for i, ch in enumerate(chars)}
    id_to_char = {i: ch for ch, i in char_to_id.items()}
    return char_to_id, id_to_char


def to_char_ids(text, char_to_id):
    """把字符串逐字符翻译成 id 列表。"""
    return [char_to_id[ch] for ch in text]


def most_frequent_pair(ids):
    """统计相邻 id 对,返回出现次数最高的 ((left, right), count)。"""
    pairs = Counter(zip(ids, ids[1:]))
    if not pairs:
        return (-1, -1), 0
    return pairs.most_common(1)[0]


def merge_pair(ids, left, right, new_id):
    """一趟从左到右的扫描:相邻的 (left, right) 一律合并成 new_id。"""
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
    """训练 BPE:反复挑最高频字对合并,记录 merges 与 pieces 拼装表。"""
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


def main() -> None:
    text = clean_text(CORPUS)
    char_to_id, id_to_char = build_char_vocab(text)
    merges, pieces = learn_bpe(text, 10, char_to_id)
    print(f"BPE 训练完成:基础词表 {len(char_to_id)} 字符,合并 {len(merges)} 条")
    print("== 前 6 条合并规则 ==")
    for i, (l, r, cnt) in enumerate(merges[:6], 1):
        piece = pieces[len(char_to_id) + i - 1]
        print(f"  #{i} 「{pieces[l]}」+「{pieces[r]}」 → 「{piece}」(出现 {cnt} 次)")
    ids = to_char_ids(text, char_to_id)
    for idx, (l, r, _c) in enumerate(merges):
        ids = merge_pair(ids, l, r, len(char_to_id) + idx)
    print(f"最终 token 数: {len(ids)}")


if __name__ == "__main__":
    main()
