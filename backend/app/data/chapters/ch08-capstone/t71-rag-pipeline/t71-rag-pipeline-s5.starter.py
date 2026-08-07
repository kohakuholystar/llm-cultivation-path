"""渡劫飞升 · s5:多路召回与融合重排

把单路检索升级为「多路召回 + RRF 融合」:先改写问题为多路查询
(真实模式交给模型,剧本模式返回固定改写),每路各取 top-k,
再用倒数排名融合把多路排名合并成一份最终候选,供生成链路使用。
"""
import os, re, sys
from collections import Counter, defaultdict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

MOCK = os.environ.get("MOCK_LLM") == "1"  # 离线演示模式

if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[渡劫飞升] 未检测到 OPENAI_API_KEY。请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

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


def clean_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text)


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n") if p.strip()]


def tokenize(text: str) -> list[str]:
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
        base = len(self.chunks)
        self.chunks.extend(chunks)
        for offset, chunk in enumerate(chunks):
            for token in tokenize(chunk.text):
                self.index[token].add(base + offset)

    def search(self, query: str, top_k: int = 3) -> list[tuple[Chunk, int]]:
        scores: Counter = Counter()
        for token in tokenize(query):
            for ci in self.index.get(token, ()):
                scores[ci] += 1
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return [(self.chunks[i], score) for i, score in ranked[:top_k]]


def build_llm() -> ChatOpenAI:
    """装配 DeepSeek 客户端(OpenAI 兼容协议)。"""
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        temperature=0,
    )


def expand_queries(question: str) -> list[str]:
    """把一个问题改写成多路查询:真实模式交给模型,剧本模式返回固定改写。"""
    # TODO: MOCK 分支返回固定改写列表;真实分支拼改写提示词调模型,回复逐行拆解去空白后取前 3 条
    # 提示: MOCK 时 return [question, "渡劫飞升 五层架构 分层", "渡劫飞升 部署 健康检查"];真实分支 build_llm().invoke([HumanMessage(content=prompt)]) 后按行拆分
    raise NotImplementedError("t71-rag-pipeline-s5 尚未实现:请按 TODO 提示完成 expand_queries 多路改写")


def fuse(retriever: Retriever, queries: list[str], top_k: int = 3) -> list[tuple[Chunk, float]]:
    """多路召回 + 倒数排名融合:每路各取 top_k,按 1/(rank+1) 跨查询累加。"""
    # TODO: 以片段对象为键,对每路 top-k 累加倒数排名分,排序后取前 top_k
    # 提示: defaultdict(float);enumerate(retriever.search(query, top_k=top_k)) 取 (rank, (chunk, _));fused[chunk] += 1.0 / (rank + 1);排序键 (-score, chunk.index)
    raise NotImplementedError("t71-rag-pipeline-s5 尚未实现:请按 TODO 提示完成 fuse 融合打分")


def multi_ask(retriever: Retriever, question: str) -> str:
    """多路问答:改写查询 -> 融合召回 -> 拼提示词 -> 生成。"""
    queries = expand_queries(question)
    print(f"多路召回:{len(queries)} 条查询,融合后候选:")
    hits = fuse(retriever, queries)
    for rank, (chunk, score) in enumerate(hits, 1):
        print(f"  #{rank}(融合分 {score:.3f}) {chunk.title}")
    prompt = build_prompt(question, hits)
    if MOCK:
        print("[MOCK] 使用剧本模拟模型回答")
        titles = sorted({c.title for c, _ in hits})
        return f"综合《{'》、《'.join(titles)}》,渡劫飞升采用五层分层架构,支持 Docker Compose 一键部署。[1]"
    resp = build_llm().invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
    return resp.content


SYSTEM_PROMPT = "你是「渡劫飞升」知识库助手。只依据提供的资料回答,并标注引用来源;资料没有的就直说不知道。"


def build_prompt(question: str, hits: list[tuple[Chunk, float]]) -> str:
    """把融合后的片段编号拼进提示词,约束模型只依据资料作答。"""
    parts = [f"[{i}]《{chunk.title}》: {chunk.text}" for i, (chunk, _) in enumerate(hits, 1)]
    return "以下是知识库资料:\n" + "\n".join(parts) + f"\n\n问题:{question}\n请结合资料回答,并注明 [i] 来源。"


def main() -> None:
    retriever = Retriever()
    for title, content in RAW_DOCS:
        retriever.add_chunks(chunk_document(title, content))
    answer = multi_ask(retriever, "渡劫飞升怎么部署,架构有什么特点?")
    print(f"\n[回答] {answer}")


if __name__ == "__main__":
    main()
