"""t60 · s1:语料清洗与字符统计

袖里乾坤的第一步,是为微型 GPT 准备「口粮」:把散落的古诗语料
清洗成规整文本,统计每个字符的出现频率,再建立字符与序号之间的
双向映射——这就是最朴素的词表(char vocab)。
"""
from collections import Counter

# 三首古诗拼成的语料:前两首各重复两遍,保证字对有足够频次
CORPUS = (
    "床前明月光,疑是地上霜。举头望明月,低头思故乡。"
    "床前明月光,疑是地上霜。举头望明月,低头思故乡。"
    "白日依山尽,黄河入海流。欲穷千里目,更上一层楼。"
)


def _is_printable(ch: str) -> bool:
    """单字是否保留:只留可打印字符(汉字、中文标点),滤掉控制符。"""
    return ch.isprintable()


def clean_text(text: str) -> str:
    """清洗语料:剔除全角空格与不可打印字符,返回纯净字符串。"""
    text = text.replace("\u3000", "")
    # TODO: 用 _is_printable(ch) 过滤不可打印字符,拼接后返回干净字符串
    # 提示: "".join(ch for ch in text if _is_printable(ch))
    raise NotImplementedError("t60-tokenizer-data-s1 尚未实现:请按 TODO 提示过滤不可打印字符并返回拼接结果")


def char_stats(text: str) -> Counter:
    """统计每个字符出现的次数,返回 Counter。"""
    return Counter(text)


def freq_table(text: str, k: int = 5) -> list:
    """按频次从高到低取前 k 个 (字符, 次数) 对。"""
    return char_stats(text).most_common(k)


def build_char_vocab(text: str):
    """按字典序建立词表,返回 char_to_id 与 id_to_char 双向映射。"""
    chars = sorted(set(text))
    # TODO: 建立 char_to_id(字符→序号)与 id_to_char(序号→字符)两个字典并返回
    # 提示: char_to_id = {ch: i for i, ch in enumerate(chars)};
    #       id_to_char = {i: ch for ch, i in char_to_id.items()}
    raise NotImplementedError("t60-tokenizer-data-s1 尚未实现:请按 TODO 提示建立双向映射字典并返回")


def to_char_ids(text: str, char_to_id: dict) -> list:
    """把字符串逐字符翻译成 id 列表。"""
    return [char_to_id[ch] for ch in text]


def main() -> None:
    """主流程:清洗 → 统计 → 建表 → 编码,并打印摘要。"""
    # 一条龙:清洗 → 建表 → 编码,顺便看一眼频次分布
    text = clean_text(CORPUS)
    char_to_id, id_to_char = build_char_vocab(text)
    # 交叉校验:频次之和应等于语料总字符数,确保统计没有漏掉任何字
    assert sum(char_stats(text).values()) == len(text)
    print(f"语料长度: {len(text)} 个字符")
    print(f"词表大小: {len(char_to_id)} 个字符")
    print("== 字符频次 TOP5 ==")
    for ch, cnt in freq_table(text, 5):
        print(f"  「{ch}」 x{cnt}")
    # 把清洗好的全文逐字转成 id,作为后续训练语料的雏形
    ids = to_char_ids(text, char_to_id)
    print(f"编码示例(前 8 个 id): {ids[:8]}")


if __name__ == "__main__":
    main()
