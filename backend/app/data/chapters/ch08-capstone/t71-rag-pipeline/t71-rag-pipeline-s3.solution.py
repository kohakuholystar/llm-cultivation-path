"""终期交付 · s3:倒排检索器

用「字符二元组」给中文文本建立倒排索引,查询时按命中 token 数打分,
返回 top-k 个 (Chunk, 分数)。本步检索完全本地、完全确定,是整条
管道里唯一不依赖大模型的环节,也是 s4 生成链路的上游。
"""
import re
from collections import Counter, defaultdict

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
    return [(title, content) for title, content in RAW_DOCS]


def clean_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def split_paragraphs(text: str) -> list[str]:
    return [para.strip() for para in text.split("\n") if para.strip()]


def tokenize(text: str) -> list[str]:
    """字符二元组切分:去标点空白后取每相邻两字符作为检索词。"""
    compact = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text.lower())
    return [compact[i:i + 2] for i in range(len(compact) - 1)]


class Chunk:
    """检索片段:正文 + 出处标题 + 文档内序号。"""

    def __init__(self, title: str, text: str, index: int):
        self.title, self.text, self.index = title, text, index

    def __repr__(self) -> str:
        return f"《{self.title}[{self.index}]》{self.text}"


def chunk_document(title: str, content: str, max_chars: int = 120, overlap: int = 20) -> list[Chunk]:
    paras = split_paragraphs(clean_text(content))
    chunks: list[Chunk] = []
    buffer = ""
    for para in paras:
        if buffer and len(buffer) + len(para) + 1 > max_chars:
            chunks.append(Chunk(title, buffer, len(chunks)))
            buffer = buffer[-overlap:] if overlap > 0 else ""
        buffer = f"{buffer}\n{para}" if buffer else para
    if buffer:
        chunks.append(Chunk(title, buffer, len(chunks)))
    return chunks


class Retriever:
    """倒排索引检索器:token -> 片段编号集合,查询按命中数打分取 top-k。"""

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.index: dict[str, set[int]] = defaultdict(set)

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """把一批片段写进索引;同一个 token 出现在多个片段时编号都记下。"""
        base = len(self.chunks)
        self.chunks.extend(chunks)
        for offset, chunk in enumerate(chunks):
            for token in tokenize(chunk.text):
                self.index[token].add(base + offset)

    def search(self, query: str, top_k: int = 3) -> list[tuple[Chunk, int]]:
        """打分检索:命中 token 越多分越高,取前 top_k 返回 (片段, 分数)。"""
        scores: Counter = Counter()
        for token in tokenize(query):
            for ci in self.index.get(token, ()):
                scores[ci] += 1
        # 分数降序、编号升序,保证同分片段顺序稳定
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return [(self.chunks[i], score) for i, score in ranked[:top_k]]


def main() -> None:
    retriever = Retriever()
    for title, content in load_docs():
        retriever.add_chunks(chunk_document(title, content))
    print(f"检索器就绪:共 {len(retriever.chunks)} 个片段,索引 {len(retriever.index)} 个词")
    query = "黑糖资料室的架构分为哪几层?"
    print(f"\n== 查询: {query} ==")
    for rank, (chunk, score) in enumerate(retriever.search(query), 1):
        print(f"#{rank} (score {score}) {chunk}")


if __name__ == "__main__":
    main()
