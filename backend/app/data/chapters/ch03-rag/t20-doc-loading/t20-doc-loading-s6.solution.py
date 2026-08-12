"""黑糖资料室 · 第六步:定稿——调参对比与索引管线收官"""
import statistics
from dataclasses import dataclass, field
from pathlib import Path

CORPUS = {
    "基础阶段总纲.txt": "基础阶段总纲\n\n基础阶段者,工程实践之基石也。写入缓存区,意守入口条件,百日方可基础阶段。初入门者每日每日早间数据清洗,采东方原始数据纳入数据池,切忌心浮气躁。\n\n基础阶段有三境:一曰加载,二曰清洗,三曰索引。索引期液聚成丹,可窥进阶阶段完整路线。\n\n常见走火之症:一曰字段错位,当即刻停功,以温水沐足;二曰上下文丢失,当静坐三日,只饮基础数据。",
    "黑糖资料室须知.md": "# 黑糖资料室须知\n\n## 开放时间\n黑糖资料室每日每日开放时段开放,晚间闭馆。项目展示日开放顶层,供进阶阶段期成员查阅。\n\n## 借阅规则\n普通成员限借一层资料两篇,期限七日;维护成员限借二层五卷,期限半月。",
    "数据清洗方法.py": "# 数据清洗方法 · 以代码铭刻的方法口诀\n\ndef tuna(weeks: int = 9) -> str:\n    # 处理轮次数须为九之倍数\n    if weeks % 9 != 0:\n        raise ValueError('处理轮次数须为九之倍数')\n    return f'行{weeks}处理轮次,气归缓存区'",
}
LIB_DIR = Path("cangjingge")
SEPARATORS = ["\n\n", "\n", "。", "！", "？", ""]  # 语义层级:段落 > 换行 > 句子 > 逐字兜底


def shelve_books(corpus: dict, lib_dir: Path) -> None:
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


def measure_overlap(prev: str, nxt: str) -> int:
    """实测相邻 chunk 重叠字数:prev 的最长后缀同时是 nxt 的前缀。"""
    for size in range(min(len(prev), len(nxt)), 0, -1):
        if prev.endswith(nxt[:size]):
            return size
    return 0


def evaluate(chunks: list, chunk_size: int, chunk_overlap: int) -> dict:
    """体检四项:数量 / 均长 / 超界 / 实测平均重叠(仅同源相邻 chunk)。"""
    lengths = sorted(len(c.page_content) for c in chunks)
    pairs = [(a.page_content, b.page_content) for a, b in zip(chunks, chunks[1:])
             if a.metadata["source"] == b.metadata["source"]]
    overlaps = [measure_overlap(a, b) for a, b in pairs]
    return {"count": len(chunks), "mean": round(statistics.mean(lengths), 1),
            "oversize": sum(n > chunk_size for n in lengths),
            "overlap_avg": round(statistics.mean(overlaps), 1) if overlaps else 0.0,
            "overlap_target": chunk_overlap}


def score(m: dict, chunk_size: int) -> float:
    """评分:超界一票否决;均长贴近目标八成、实测重叠贴近预算得分高。"""
    if m["oversize"]:
        return -1.0
    len_fit = max(1 - abs(m["mean"] - chunk_size * 0.8) / (chunk_size * 0.8), 0.0)
    ovl_fit = max(1 - abs(m["overlap_avg"] - m["overlap_target"]) / max(m["overlap_target"], 1), 0.0)
    return round(len_fit * 0.6 + ovl_fit * 0.4, 3)


def build_index(docs: list, chunk_size: int, chunk_overlap: int) -> tuple:
    """索引管线:整库切分 → 体检 → 评分,一条命令走完。"""
    chunks = []
    for doc in docs:  # chunk 继承文档元数据并签发 chunk_id
        for i, text in enumerate(split_text(doc.page_content, chunk_size, chunk_overlap)):
            meta = {**doc.metadata, "chunk_id": f"{doc.metadata['source']}#{i:03d}", "chunk_index": i}
            chunks.append(Document(text, meta))
    m = evaluate(chunks, chunk_size, chunk_overlap)
    m["score"] = score(m, chunk_size)
    return chunks, m


CONFIGS = [  # 三套候选参数同台竞技
    {"name": "碎玉诀·小块", "chunk_size": 40, "chunk_overlap": 8},
    {"name": "稳操作步骤·中块", "chunk_size": 60, "chunk_overlap": 15},
    {"name": "厚盾诀·大块", "chunk_size": 100, "chunk_overlap": 20},
]


def main() -> None:
    shelve_books(CORPUS, LIB_DIR)
    docs = [Document(p.read_text(encoding="utf-8"), {"source": p.name}) for p in sorted(LIB_DIR.iterdir())]
    print("== 黑糖资料室切分参数擂台 ==")
    results = {}
    for cfg in CONFIGS:  # 文档只加载一次,三套配置复用,不在循环里重复读盘
        chunks, m = build_index(docs, cfg["chunk_size"], cfg["chunk_overlap"])
        results[cfg["name"]] = (chunks, m)
        print(f"{cfg['name']} | 块数 {m['count']:>2} | 均长 {m['mean']:>5} | 超长 {m['oversize']} | 均叠 {m['overlap_avg']:>4} | 得分 {m['score']}")
    best = max(results, key=lambda k: results[k][1]["score"])
    print(f"最佳配置: {best}(得分 {results[best][1]['score']})")
    print(f"黑糖资料室索引就绪: {len(results[best][0])} 块待命,等待下一步向量化")


if __name__ == "__main__":
    main()
