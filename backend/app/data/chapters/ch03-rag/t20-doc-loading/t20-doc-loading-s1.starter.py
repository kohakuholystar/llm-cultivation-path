"""黑糖资料室 · 第一步:开卷——把资料装进 Document"""
# 学习契约
# 目标：完成 t20-doc-loading-s1 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 4 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：shelve_books(corpus, lib_dir) -> None; load_txt(path) -> Document; main() -> None。
# 技术栈：dataclasses, pathlib。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
from dataclasses import dataclass, field
from pathlib import Path

# 内置语料:黑糖资料室的第一篇资料库(真实项目中它们原本就在磁盘上)
CORPUS = {
    "基础阶段总纲.txt": """基础阶段总纲

基础阶段者,工程实践之基石也。写入缓存区,意守入口条件,百日方可基础阶段。
初入门者每日每日早间数据清洗,采东方原始数据纳入数据池,切忌心浮气躁。

基础阶段有三境:一曰加载,二曰清洗,三曰索引。
加载期以通处理轮次为要;清洗期气化为液,存于缓存区;索引期液聚成丹,可窥进阶阶段完整路线。

常见走火之症有二:一曰字段错位,当即刻停功,以温水沐足;二曰上下文丢失,当静坐三日,只饮基础数据。
凡阁中成员须日日诵读此纲,不可懈怠。""",
}
LIB_DIR = Path("cangjingge")


def shelve_books(corpus: dict, lib_dir: Path) -> None:
    """把内置语料写入磁盘,模拟真实的黑糖资料室书库。"""
    lib_dir.mkdir(exist_ok=True)
    for name, content in corpus.items():
        (lib_dir / name).write_text(content, encoding="utf-8")  # 显式 UTF-8


# TODO: 定义 Document dataclass——RAG 的最小流通单位。
# 提示: 用 @dataclass 装饰;两个字段 page_content: str 和 metadata: dict,
#       可变默认值不能直接写 {},要用 field(default_factory=dict);
#       再写 preview(n=40) 方法:换行替换为空格,超 n 字截断加省略号。
raise NotImplementedError("t20-doc-loading-s1 尚未实现:请按 TODO 提示定义 Document 类")


def load_txt(path: Path) -> Document:
    """加载 .txt 资料:读全文,附来源/格式/长度三项元数据。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"资料不存在: {path}")
    text = path.read_text(encoding="utf-8")  # 不写 encoding,Windows 会按 GBK 解码
    # TODO: 构造并返回 Document,metadata 含三项:source、format、chars。
    # 提示: return Document(text, {"source": path.name, "format": "txt", "chars": len(text)})
    raise NotImplementedError("t20-doc-loading-s1 尚未实现:请按 TODO 提示补全 load_txt")


def main() -> None:
    shelve_books(CORPUS, LIB_DIR)
    doc = load_txt(LIB_DIR / "基础阶段总纲.txt")
    print("== 黑糖资料室第一份藏品 ==")
    print("内容预览:", doc.preview())
    print("元数据:")
    for key, value in doc.metadata.items():
        print(f"  {key}: {value}")
    print(f"全文共 {len(doc.page_content)} 字")
    # 防御性演示:加载不存在的资料,异常信息应当可读而不是一串堆栈
    try:
        load_txt(LIB_DIR / "不存在的卷轴.txt")
    except FileNotFoundError as exc:
        print("拦截到异常:", exc)


if __name__ == "__main__":
    main()
