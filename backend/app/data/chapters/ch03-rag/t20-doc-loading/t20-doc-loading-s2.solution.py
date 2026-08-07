"""藏经阁 · 第二步:多格式入藏——txt/md/代码各配一把钥匙"""
import ast
from dataclasses import dataclass, field
from pathlib import Path

CORPUS = {
    "筑基总纲.txt": "筑基总纲\n\n筑基者,仙道之基石也。气沉丹田,意守玄关,百日方可筑基。初入门者每日卯时吐纳,采东方紫气纳入气海,切忌心浮气躁。\n\n筑基有三境:一曰引气,二曰凝液,三曰化丹。化丹期液聚成丹,可窥金丹大道。\n\n常见走火之症:一曰气逆,当即刻停功,以温水沐足;二曰神散,当静坐三日,只饮清泉。",
    "藏经阁须知.md": "# 藏经阁须知\n\n## 开放时间\n藏经阁每日辰时开放,戌时闭馆。月圆之夜开放顶层,供金丹期弟子参悟。\n\n## 借阅规则\n外门弟子限借一层典籍两卷,期限七日;内门弟子限借二层五卷,期限半月。",
    "吐纳心法.py": "# 吐纳心法 · 以代码铭刻的功法口诀\n\ndef tuna(weeks: int = 9) -> str:\n    # 周天数须为九之倍数\n    if weeks % 9 != 0:\n        raise ValueError('周天数须为九之倍数')\n    return f'行{weeks}周天,气归丹田'",
}
LIB_DIR = Path("cangjingge")


def shelve_books(corpus: dict, lib_dir: Path) -> None:
    """把内置语料写入磁盘,模拟真实的藏经阁书库。"""
    lib_dir.mkdir(exist_ok=True)
    for name, content in corpus.items():
        (lib_dir / name).write_text(content, encoding="utf-8")


@dataclass
class Document:
    """RAG 的最小流通单位:一段文本 + 它的出身证明(元数据)。"""

    page_content: str
    metadata: dict = field(default_factory=dict)


def _load_txt(path: Path) -> Document:
    """纯文本:无结构可挖,记下长度即可。"""
    text = path.read_text(encoding="utf-8")
    return Document(text, {"source": path.name, "format": "txt", "chars": len(text)})


def _load_md(path: Path) -> Document:
    """Markdown:标题是天然的语义锚点,务必提取。"""
    text = path.read_text(encoding="utf-8")
    title = next((ln[2:] for ln in text.splitlines() if ln.startswith("# ")), "无标题")
    headings = sum(1 for ln in text.splitlines() if ln.startswith("#"))
    return Document(text, {"source": path.name, "format": "md", "chars": len(text),
                           "title": title, "headings": headings})


def _load_py(path: Path) -> Document:
    """代码:函数是它的骨架,用 AST 数出来。"""
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)  # 语法错误会直接抛 SyntaxError,暴露问题比静默吞掉好
    functions = sum(isinstance(n, ast.FunctionDef) for n in ast.walk(tree))
    return Document(text, {"source": path.name, "format": "py", "chars": len(text),
                           "functions": functions})


LOADERS = {".txt": _load_txt, ".md": _load_md, ".py": _load_py}  # 分发表


def load_document(path: Path) -> Document:
    """统一入口:按扩展名分发到对应格式的加载器。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"典籍不存在: {path}")
    loader = LOADERS.get(path.suffix.lower())  # 扩展名统一小写再查表
    if loader is None:
        raise ValueError(f"不支持的典籍格式: {path}")  # fail-fast,绝不静默降级
    return loader(path)


def load_directory(lib_dir: Path) -> list:
    """整库入藏,按文件名排序保证结果稳定可复现。"""
    return [load_document(p) for p in sorted(Path(lib_dir).iterdir()) if p.suffix.lower() in LOADERS]


def main() -> None:
    shelve_books(CORPUS, LIB_DIR)
    docs = load_directory(LIB_DIR)
    print("== 藏经阁书目 ==")
    for doc in docs:
        m = doc.metadata
        print(f"✔ {m['source']} [{m['format']}] {m['chars']} 字 | {m}")
    print(f"共入藏 {len(docs)} 卷典籍,合计 {sum(d.metadata['chars'] for d in docs)} 字")
    # 不支持的格式必须当面拒绝,而不是混进知识库污染下游
    (LIB_DIR / "丹方.pdf").write_text("fake pdf bytes", encoding="utf-8")
    try:
        load_document(LIB_DIR / "丹方.pdf")
    except ValueError as exc:
        print("✘ 拒绝入藏:", exc)


if __name__ == "__main__":
    main()
