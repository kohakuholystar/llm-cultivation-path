"""渡劫飞升 · s2:重叠切分器

在 s1 清洗后的段落之上,把每篇文档切成一串不超过 max_chars 字符、
相邻片段首尾重叠 overlap 字符的小片段,并让每个片段携带出处元数据。
这些片段就是检索的最小单元:召回、打分、引用都发生在片段粒度。
"""
import re

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
    return [(title, content) for title, content in RAW_DOCS]


def clean_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def split_paragraphs(text: str) -> list[str]:
    return [para.strip() for para in text.split("\n") if para.strip()]


class Chunk:
    """检索片段:正文 + 出处标题 + 文档内序号。"""

    def __init__(self, title: str, text: str, index: int):
        self.title = title   # 出自哪篇文档
        self.text = text     # 片段正文
        self.index = index   # 在文档内的顺序号,从 0 起

    def __repr__(self) -> str:
        return f"《{self.title}[{self.index}]》{self.text}"


def chunk_document(title: str, content: str, max_chars: int = 120, overlap: int = 20) -> list[Chunk]:
    """把一篇文档切成有重叠的片段:buffer 攒段落,超长就收片并携带尾部重叠。"""
    paras = split_paragraphs(clean_text(content))
    chunks: list[Chunk] = []
    buffer = ""
    for para in paras:
        if buffer and len(buffer) + len(para) + 1 > max_chars:
            # TODO: 收片并携带尾部重叠,补两行
            # 提示: 用 Chunk(title, buffer, len(chunks)) 收片;再取 buffer[-overlap:](overlap>0 时)作为下一片的开头
            raise NotImplementedError("t71-rag-pipeline-s2 尚未实现:请按 TODO 提示收片并携带重叠")
        buffer = f"{buffer}\n{para}" if buffer else para
    if buffer:
        chunks.append(Chunk(title, buffer, len(chunks)))
    return chunks


def main() -> None:
    docs = load_docs()
    total = 0
    for title, content in docs:
        chunks = chunk_document(title, content)
        total += len(chunks)
        print(f"《{title}》 -> {len(chunks)} 个片段")
    print(f"切分完成:共 {total} 个片段,相邻片段首尾重叠 20 字符")
    for i, chunk in enumerate(chunk_document(docs[1][0], docs[1][1])[:2]):
        print(f"  样例 {i}: {chunk}")


if __name__ == "__main__":
    main()
