"""黑糖资料室 · 第三步:动刀——手写递归字符切分器"""
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
    """把内置语料写入磁盘,模拟真实的黑糖资料室书库。"""
    lib_dir.mkdir(exist_ok=True)
    for name, content in corpus.items():
        (lib_dir / name).write_text(content, encoding="utf-8")


@dataclass
class Document:
    """RAG 的最小流通单位:一段文本 + 它的出身证明(元数据)。"""

    page_content: str
    metadata: dict = field(default_factory=dict)

    def preview(self, n: int = 40) -> str:
        """单行预览,便于打印 chunk 清单。"""
        text = self.page_content.replace("\n", " ")
        return text[:n] + ("..." if len(text) > n else "")


def load_document(path: Path) -> Document:
    """统一加载入口:读文本 + 记录来源/格式/长度(本步聚焦切分,元数据从简)。"""
    text = path.read_text(encoding="utf-8")
    meta = {"source": path.name, "format": path.suffix.lstrip("."), "chars": len(text)}
    return Document(text, meta)


def _merge_splits(pieces: list, sep: str, chunk_size: int, chunk_overlap: int) -> list:
    """顺序装箱:装满 chunk_size 即封箱,箱尾按重叠预算留给下一箱。"""
    chunks, current, size = [], [], 0
    for piece in pieces:
        if current and size + len(piece) + len(sep) > chunk_size:
            chunks.append(sep.join(current))  # 封箱
            while current and size > chunk_overlap:  # 从箱头丢弃,箱尾留作重叠
                size -= len(current.pop(0)) + (len(sep) if current else 0)
        current.append(piece)
        size += len(piece) + (len(sep) if len(current) > 1 else 0)
    if current:
        chunks.append(sep.join(current))
    return chunks


def split_text(text: str, chunk_size: int = 60, chunk_overlap: int = 15,
               separators: list = SEPARATORS) -> list:
    """递归字符切分:优先在最高层分隔符处断开,超长块降级到下一层再切。"""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须小于 chunk_size")
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    sep = next((s for s in separators if s == "" or s in text), "")  # 最高可用层级
    pieces = text.split(sep) if sep else list(text)  # 兜底:逐字硬切
    deeper = separators[separators.index(sep) + 1:] or [""]  # 下一层分隔符
    chunks = []
    for block in _merge_splits(pieces, sep, chunk_size, chunk_overlap):
        if len(block) > chunk_size:
            chunks.extend(split_text(block, chunk_size, chunk_overlap, deeper))  # 递归降级
        else:
            chunks.append(block)
    return [c for c in chunks if c.strip()]


def split_documents(docs: list, chunk_size: int = 60, chunk_overlap: int = 15) -> list:
    """整库切分:chunk 继承原文档元数据并追加序号。"""
    chunks = []
    for doc in docs:
        for i, text in enumerate(split_text(doc.page_content, chunk_size, chunk_overlap)):
            chunks.append(Document(text, {**doc.metadata, "chunk_index": i}))
    return chunks


def main() -> None:
    shelve_books(CORPUS, LIB_DIR)
    docs = [load_document(p) for p in sorted(LIB_DIR.iterdir())]
    chunks = split_documents(docs, chunk_size=60, chunk_overlap=15)
    print("== 切分结果 ==")
    for c in chunks:
        m = c.metadata
        print(f"[{m['source']}#{m['chunk_index']}] {len(c.page_content):>2} 字 | {c.preview(20)}")
    print(f"共切出 {len(chunks)} 块")
    longest = max(len(c.page_content) for c in chunks)
    assert longest <= 60, "递归切分违约:出现超界块"
    print(f"最长块 {longest} 字,未超 60 字上限")


if __name__ == "__main__":
    main()
