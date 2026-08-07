"""渡劫飞升 · s1:知识库文档加载与清洗

毕业设计「渡劫飞升」的第一块基石:把三篇项目文档读进内存,
清洗掉全角空格、多余空白与空行,再按段落切分,并统计入库规模。
本步纯标准库实现,无需联网,是整条 RAG 管道的离线地基。
"""
import re

# 项目知识库原始语料:(标题, 正文),模拟从磁盘读到的三篇 Markdown
RAW_DOCS = [
    ("需求分析.md",
     "渡劫飞升是一款面向修仙者的 AI 助手应用。\n"
     "核心功能:修炼咨询、丹药百科、宗门问答、渡劫指引。\n"
     "要求回答准确、引用出处、支持多轮追问。"),
    ("架构设计.md",
     "渡劫飞升采用分层架构,共五层。\n"
     "接入层用 FastAPI 提供 HTTP 接口;ingest 层负责加载切分入库。\n"
     "检索层把问题向量化后召回片段;生成层拼装提示词调用大模型。"),
    ("部署手册.md",
     "渡劫飞升支持 Docker Compose 一键部署,服务暴露 8000 端口。\n"
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
