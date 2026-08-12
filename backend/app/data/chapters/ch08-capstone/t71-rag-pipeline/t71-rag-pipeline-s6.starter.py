"""终期交付 · s6:总装成器——知识库问答模块

把 s1-s5 的加载、清洗、切分、检索、多路召回与生成,封装成对外只暴露
ingest()/ask() 两个方法的 KnowledgeBase,并提供可交互的 CLI 循环。
至此,「终期交付」的知识库问答模块以生产级形态交付。
"""


# === 学习契约（面向学生）===
# 本节目标：总装成器:知识库问答模块。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `clean_text(text: str) -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `split_paragraphs(text: str) -> list[str]`：输入为签名中的参数；输出为 `list[str]`。用途：按本节调用链完成对应处理
#   - `tokenize(text: str) -> list[str]`：输入为签名中的参数；输出为 `list[str]`。用途：按本节调用链完成对应处理
#   - `chunk_document(title: str, content: str, max_chars: int=120, overlap: int=20) -> list[Chunk]`：输入为签名中的参数；输出为 `list[Chunk]`。用途：按本节调用链完成对应处理
#   - `build_llm() -> ChatOpenAI`：输入为签名中的参数；输出为 `ChatOpenAI`。用途：按本节调用链完成对应处理
#   - `build_prompt(question: str, hits: list[tuple[Chunk, float]]) -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `expand_queries(question: str) -> list[str]`：输入为签名中的参数；输出为 `list[str]`。用途：按本节调用链完成对应处理
#   - `fuse(retriever: Retriever, queries: list[str], top_k: int=3) -> list[tuple[Chunk, float]]`：输入为签名中的参数；输出为 `list[tuple[Chunk, float]]`。用途：按本节调用链完成对应处理
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Chunk`：承载本节状态/数据；重点方法：见类定义。
#   - `Retriever`：承载本节状态/数据；重点方法：add_chunks, search。
#   - `KnowledgeBase`：承载本节状态/数据；重点方法：ingest, ask, cli。
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import os, re, sys
from collections import Counter, defaultdict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

MOCK = os.environ.get("MOCK_LLM") == "1"  # 离线演示模式

if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[黑糖资料室] 未检测到 OPENAI_API_KEY。请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

RAW_DOCS = [
    ("需求分析.md", "黑糖资料室是一款面向学习者的 AI 助手应用。\n核心功能:学习咨询、活动方案百科、项目组问答、上线验收指引。\n要求回答准确、引用出处、支持多轮追问。"),
    ("架构设计.md", "黑糖资料室采用分层架构,共五层。\n接入层用 FastAPI 提供 HTTP 接口;ingest 层负责加载切分入库。\n检索层把问题向量化后召回片段;生成层拼装提示词调用大模型。"),
    ("部署手册.md", "黑糖资料室支持 Docker Compose 一键部署,服务暴露 8000 端口。\n健康检查路径 /healthz 返回 ok 即部署成功。\n环境变量 LLM_API_KEY 指定大模型密钥,DATABASE_URL 指定向量库。"),
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
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        temperature=0,
    )


SYSTEM_PROMPT = "你是「黑糖资料室」知识库助手。只依据提供的资料回答,并标注引用来源;资料没有的就直说不知道。"


def build_prompt(question: str, hits: list[tuple[Chunk, float]]) -> str:
    parts = [f"[{i}]《{chunk.title}》: {chunk.text}" for i, (chunk, _) in enumerate(hits, 1)]
    return "以下是知识库资料:\n" + "\n".join(parts) + f"\n\n问题:{question}\n请结合资料回答,并注明 [i] 来源。"


def expand_queries(question: str) -> list[str]:
    if MOCK:
        return [question, "黑糖资料室 五层架构 分层", "黑糖资料室 部署 健康检查"]
    prompt = ("把下面这个问题改写成 2 个不同角度的检索查询,每行一个,不要编号:\n" + question)
    text = build_llm().invoke([HumanMessage(content=prompt)]).content
    return [q.strip() for q in text.splitlines() if q.strip()][:3]


def fuse(retriever: Retriever, queries: list[str], top_k: int = 3) -> list[tuple[Chunk, float]]:
    fused: dict[Chunk, float] = defaultdict(float)
    for query in queries:
        for rank, (chunk, _score) in enumerate(retriever.search(query, top_k=top_k)):
            fused[chunk] += 1.0 / (rank + 1)
    ranked = sorted(fused.items(), key=lambda kv: (-kv[1], kv[0].index))
    return ranked[:top_k]


class KnowledgeBase:
    def __init__(self, max_chars: int = 120, overlap: int = 20, top_k: int = 3) -> None:
        self.max_chars, self.overlap, self.top_k = max_chars, overlap, top_k
        self.retriever = Retriever()
        self.question_count = 0

    def ingest(self, docs: list[tuple[str, str]]) -> None:
        self.retriever = Retriever()  # 幂等:旧索引作废
        for title, content in docs:
            self.retriever.add_chunks(chunk_document(title, content, self.max_chars, self.overlap))
        print(f"灌库完成:共 {len(self.retriever.chunks)} 个片段")

    def ask(self, question: str) -> tuple[str, list[str]]:
        # TODO: 补全问答链路:多路召回融合 -> 拼提示词 -> MOCK 剧本/真实模型,返回 (answer, sources)
        # 提示: expand_queries(question) 与 fuse(self.retriever, queries, self.top_k);来源取 sorted({chunk.title for chunk, _ in hits});question_count 自增;MOCK 时返回剧本回答
        raise NotImplementedError("t71-rag-pipeline-s6 尚未实现:请按 TODO 提示完成 KnowledgeBase.ask 问答链路")

    def cli(self) -> None:
        print("黑糖资料室 · 知识库问答模块(输入空行或退出结束)")
        # TODO: 写 while True 交互循环:空输入或命中 退出/quit/exit 结束并打印告别语,否则问答
        # 提示: input("你: ").strip();结束条件 not question or question in ("退出", "quit", "exit");调 self.ask 后打印 助手/引用
        raise NotImplementedError("t71-rag-pipeline-s6 尚未实现:请按 TODO 提示完成 cli 交互循环")


def main() -> None:
    kb = KnowledgeBase()
    kb.ingest(RAW_DOCS)
    for q in ["黑糖资料室的架构分为哪几层?", "黑糖资料室怎么部署?"]:
        a, s = kb.ask(q)
        print(f"[Q] {q}\n[回答] {a}\n[引用] {'、'.join(s)}")
    print(f"本轮累计问答 {kb.question_count} 次;交互模式请运行 cli()")


if __name__ == "__main__":
    main()
