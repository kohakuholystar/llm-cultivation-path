"""藏经阁 · 第一步:开卷——把古籍装进 Document"""
from dataclasses import dataclass, field
from pathlib import Path

# 内置语料:藏经阁的第一卷藏书(真实项目中它们原本就在磁盘上)
CORPUS = {
    "筑基总纲.txt": """筑基总纲

筑基者,仙道之基石也。气沉丹田,意守玄关,百日方可筑基。
初入门者每日卯时吐纳,采东方紫气纳入气海,切忌心浮气躁。

筑基有三境:一曰引气,二曰凝液,三曰化丹。
引气期以通周天为要;凝液期气化为液,存于丹田;化丹期液聚成丹,可窥金丹大道。

常见走火之症有二:一曰气逆,当即刻停功,以温水沐足;二曰神散,当静坐三日,只饮清泉。
凡阁中弟子须日日诵读此纲,不可懈怠。""",
}
LIB_DIR = Path("cangjingge")


def shelve_books(corpus: dict, lib_dir: Path) -> None:
    """把内置语料写入磁盘,模拟真实的藏经阁书库。"""
    lib_dir.mkdir(exist_ok=True)
    for name, content in corpus.items():
        (lib_dir / name).write_text(content, encoding="utf-8")  # 显式 UTF-8


@dataclass
class Document:
    """RAG 的最小流通单位:一段文本 + 它的出身证明(元数据)。"""

    page_content: str
    metadata: dict = field(default_factory=dict)  # 可变默认值必须用 factory

    def preview(self, n: int = 40) -> str:
        """单行预览,超过 n 字截断加省略号。"""
        text = self.page_content.replace("\n", " ")
        return text[:n] + ("..." if len(text) > n else "")


def load_txt(path: Path) -> Document:
    """加载 .txt 古籍:读全文,附来源/格式/长度三项元数据。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"典籍不存在: {path}")
    text = path.read_text(encoding="utf-8")  # 不写 encoding,Windows 会按 GBK 解码
    return Document(text, {"source": path.name, "format": "txt", "chars": len(text)})


def main() -> None:
    shelve_books(CORPUS, LIB_DIR)
    doc = load_txt(LIB_DIR / "筑基总纲.txt")
    print("== 藏经阁第一件藏品 ==")
    print("内容预览:", doc.preview())
    print("元数据:")
    for key, value in doc.metadata.items():
        print(f"  {key}: {value}")
    print(f"全文共 {len(doc.page_content)} 字")
    # 防御性演示:加载不存在的典籍,异常信息应当可读而不是一串堆栈
    try:
        load_txt(LIB_DIR / "不存在的卷轴.txt")
    except FileNotFoundError as exc:
        print("拦截到异常:", exc)


if __name__ == "__main__":
    main()
