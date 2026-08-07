"""藏经阁 · 第五步:质检——切分质量评估(长度分布与重叠率)"""
import statistics
from dataclasses import dataclass, field
from pathlib import Path

CORPUS = {
    "筑基总纲.txt": "筑基总纲\n\n筑基者,仙道之基石也。气沉丹田,意守玄关,百日方可筑基。初入门者每日卯时吐纳,采东方紫气纳入气海,切忌心浮气躁。\n\n筑基有三境:一曰引气,二曰凝液,三曰化丹。化丹期液聚成丹,可窥金丹大道。\n\n常见走火之症:一曰气逆,当即刻停功,以温水沐足;二曰神散,当静坐三日,只饮清泉。",
    "藏经阁须知.md": "# 藏经阁须知\n\n## 开放时间\n藏经阁每日辰时开放,戌时闭馆。月圆之夜开放顶层,供金丹期弟子参悟。\n\n## 借阅规则\n外门弟子限借一层典籍两卷,期限七日;内门弟子限借二层五卷,期限半月。",
    "吐纳心法.py": "# 吐纳心法 · 以代码铭刻的功法口诀\n\ndef tuna(weeks: int = 9) -> str:\n    # 周天数须为九之倍数\n    if weeks % 9 != 0:\n        raise ValueError('周天数须为九之倍数')\n    return f'行{weeks}周天,气归丹田'",
}
LIB_DIR = Path("cangjingge")
SEPARATORS = ["\n\n", "\n", "。", "！", "？", ""]  # 语义层级:段落 > 换行 > 句子 > 逐字兜底


def shelve_books(corpus: dict, lib_dir: Path) -> None:
    """把内置语料写入磁盘,模拟真实的藏经阁书库。"""
    lib_dir.mkdir(exist_ok=True)
    for name, content in corpus.items():
        (lib_dir / name).write_text(content, encoding="utf-8")


@dataclass
class Document:
    """最小流通单位:文本 + 出身证明。"""

    page_content: str
    metadata: dict = field(default_factory=dict)


def _merge_splits(pieces: list, sep: str, chunk_size: int, chunk_overlap: int) -> list:
    """顺序装箱:装满即封箱,箱尾按重叠预算留给下一箱。"""
    chunks, current, size = [], [], 0
    for piece in pieces:
        if current and size + len(piece) + len(sep) > chunk_size:
            chunks.append(sep.join(current))
            while current and size > chunk_overlap:  # 从箱头丢弃,箱尾留作重叠
                size -= len(current.pop(0)) + (len(sep) if current else 0)
        current.append(piece)
        size += len(piece) + (len(sep) if len(current) > 1 else 0)
    if current:
        chunks.append(sep.join(current))
    return chunks


def split_text(text: str, chunk_size: int, chunk_overlap: int, separators: list = SEPARATORS) -> list:
    """递归字符切分:优先在最高层分隔符处断开,超长块降级再切。"""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    sep = next((s for s in separators if s == "" or s in text), "")
    pieces = text.split(sep) if sep else list(text)
    deeper = separators[separators.index(sep) + 1:] or [""]
    chunks = []
    for block in _merge_splits(pieces, sep, chunk_size, chunk_overlap):
        if len(block) > chunk_size:
            chunks.extend(split_text(block, chunk_size, chunk_overlap, deeper))
        else:
            chunks.append(block)
    return [c for c in chunks if c.strip()]


def split_documents(docs: list, chunk_size: int, chunk_overlap: int) -> list:
    """整库切分:chunk 继承文档元数据并追加 chunk_id 与序号。"""
    chunks = []
    for doc in docs:
        for i, text in enumerate(split_text(doc.page_content, chunk_size, chunk_overlap)):
            meta = {**doc.metadata, "chunk_id": f"{doc.metadata['source']}#{i:03d}", "chunk_index": i}
            chunks.append(Document(text, meta))
    return chunks


def measure_overlap(prev: str, nxt: str) -> int:
    """实测相邻 chunk 的重叠字数:prev 的最长后缀同时是 nxt 的前缀。"""
    for size in range(min(len(prev), len(nxt)), 0, -1):
        if prev.endswith(nxt[:size]):
            return size
    return 0


def evaluate_chunks(chunks: list, chunk_size: int, chunk_overlap: int) -> dict:
    """四维体检:规模 / 长度分布 / 超界 / 实测重叠。"""
    lengths = sorted(len(c.page_content) for c in chunks)
    # 只对同源且相邻的 chunk 测重叠;上一本书的末块与下一本书的首块毫无关系
    pairs = [(a.page_content, b.page_content) for a, b in zip(chunks, chunks[1:])
             if a.metadata["source"] == b.metadata["source"]]
    overlaps = [measure_overlap(a, b) for a, b in pairs]
    return {
        "count": len(chunks),
        "min": lengths[0], "max": lengths[-1],
        "mean": round(statistics.mean(lengths), 1),
        "median": statistics.median(lengths),
        "p90": lengths[int(len(lengths) * 0.9)],  # 九成分位:大多数块最长有多长
        "oversize": sum(n > chunk_size for n in lengths),  # 硬指标,必须为 0
        "overlap_avg": round(statistics.mean(overlaps), 1) if overlaps else 0.0,
        "overlap_target": chunk_overlap,
    }


def print_report(m: dict, chunk_size: int) -> None:
    """渲染质检报告并给出结论。"""
    print("== 切分质检报告 ==")
    print(f"chunk 总数: {m['count']} | 长度 min={m['min']} mean={m['mean']} median={m['median']} p90={m['p90']} max={m['max']}")
    print(f"超长块: {m['oversize']} 个(阈值 {chunk_size} 字,应为 0)")
    print(f"平均重叠: {m['overlap_avg']} 字(预算 {m['overlap_target']} 字)")
    print("质检结论:", "合格" if m["oversize"] == 0 else "不合格")


def main() -> None:
    shelve_books(CORPUS, LIB_DIR)
    docs = [Document(p.read_text(encoding="utf-8"), {"source": p.name}) for p in sorted(LIB_DIR.iterdir())]
    chunks = split_documents(docs, chunk_size=60, chunk_overlap=15)
    print_report(evaluate_chunks(chunks, 60, 15), 60)


if __name__ == "__main__":
    main()
