"""终期交付 · s1:知识库文档加载与清洗

毕业设计「终期交付」的第一块基石:把三篇项目文档读进内存,
清洗掉全角空格、多余空白与空行,再按段落切分,并统计入库规模。
本步纯标准库实现,无需联网,是整条 RAG 管道的离线地基。
"""


# === 学习契约（面向学生）===
# 本节目标：文档入库:加载与清洗。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `load_docs() -> list[tuple[str, str]]`：输入为签名中的参数；输出为 `list[tuple[str, str]]`。用途：把原始语料载入内存,返回 (标题, 正文) 列表。
#   - `clean_text(text: str) -> str`：输入为签名中的参数；输出为 `str`。用途：清洗正文:全角空格转半角,压缩行内空白与连续空行。
#   - `split_paragraphs(text: str) -> list[str]`：输入为签名中的参数；输出为 `list[str]`。用途：按换行把正文切成段落,逐段 strip 并丢弃空段落。
#   - `show_preview(text: str, width: int=40) -> str`：输入为签名中的参数；输出为 `str`。用途：截取正文前 width 个字符作预览,方便人工核验清洗效果。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import re

# 项目知识库原始语料:(标题, 正文),模拟从磁盘读到的三篇 Markdown
RAW_DOCS = [
    ("需求分析.md",
     "黑糖资料室是一款面向学习者的 AI 助手应用。\n"
     "核心功能:学习咨询、活动方案百科、项目组问答、上线验收指引。\n"
     "要求回答准确、引用出处、支持多轮追问。"),
    ("架构设计.md",
     "黑糖资料室采用分层架构,共五层。\n"
     "接入层用 FastAPI 提供 HTTP 接口;ingest 层负责加载切分入库。\n"
     "检索层把问题向量化后召回片段;生成层拼装提示词调用大模型。"),
    ("部署手册.md",
     "黑糖资料室支持 Docker Compose 一键部署,服务暴露 8000 端口。\n"
     "健康检查路径 /healthz 返回 ok 即部署成功。\n"
     "环境变量 LLM_API_KEY 指定大模型密钥,DATABASE_URL 指定向量库。"),
]


def load_docs() -> list[tuple[str, str]]:
    """把原始语料载入内存,返回 (标题, 正文) 列表。"""
    return [(title, content) for title, content in RAW_DOCS]


# 逐篇清洗并统计,输出人工可核验的入库报表
def clean_text(text: str) -> str:
    """清洗正文:全角空格转半角,压缩行内空白与连续空行。"""
    # TODO: 完成三步清洗:全角空格转半角、行内连续空白压成单个空格、连续空行压成单个空行,每步一行赋值
    # 提示: text.replace("\u3000", " ") 与 re.sub(r"[ \t]+", " ", ...)、re.sub(r"\n{3,}", "\n\n", ...)
    raise NotImplementedError("t71-rag-pipeline-s1 尚未实现:请按 TODO 提示完成 clean_text 三步清洗")


def split_paragraphs(text: str) -> list[str]:
    """按换行把正文切成段落,逐段 strip 并丢弃空段落。"""
    # TODO: 用一行列表推导完成切分:按换行切、逐段 strip、过滤空段落
    # 提示: [para.strip() for para in text.split("\n") if ...],先 strip 再判空
    raise NotImplementedError("t71-rag-pipeline-s1 尚未实现:请按 TODO 提示用列表推导完成 split_paragraphs")


def show_preview(text: str, width: int = 40) -> str:
    """截取正文前 width 个字符作预览,方便人工核验清洗效果。"""
    return text[:width] + ("……" if len(text) > width else "")


def main() -> None:
    docs = load_docs()
    stats = {"docs": len(docs), "paras": 0, "chars": 0}
    for title, content in docs:
        cleaned = clean_text(content)
        paras = split_paragraphs(cleaned)
        stats["paras"] += len(paras)
        stats["chars"] += len(cleaned)
        print(f"《{title}》 清洗后 {len(cleaned)} 字,{len(paras)} 个段落")
        print(f"  预览: {show_preview(cleaned)}")
    print(f"入库完成:共 {stats['docs']} 篇文档,{stats['paras']} 个段落,{stats['chars']} 字")


if __name__ == "__main__":
    main()
