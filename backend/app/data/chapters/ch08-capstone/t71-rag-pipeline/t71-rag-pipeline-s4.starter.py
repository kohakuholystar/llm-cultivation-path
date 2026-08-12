"""终期交付 · s4:检索增强生成——接入 DeepSeek 合龙问答链路

把 s3 的检索器接到大模型上:先本地召回 top-k 片段,拼进提示词,
再调用 deepseek-v4-pro 生成带引用的回答。无 API Key 时优雅退出;
设 MOCK_LLM=1 可离线用剧本跑通全链路。
"""


# === 学习契约（面向学生）===
# 本节目标：接入 DeepSeek:检索增强生成合龙。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `load_docs() -> list[tuple[str, str]]`：输入为签名中的参数；输出为 `list[tuple[str, str]]`。用途：按本节调用链完成对应处理
#   - `clean_text(text: str) -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `split_paragraphs(text: str) -> list[str]`：输入为签名中的参数；输出为 `list[str]`。用途：按本节调用链完成对应处理
#   - `tokenize(text: str) -> list[str]`：输入为签名中的参数；输出为 `list[str]`。用途：按本节调用链完成对应处理
#   - `chunk_document(title: str, content: str, max_chars: int=120, overlap: int=20) -> list[Chunk]`：输入为签名中的参数；输出为 `list[Chunk]`。用途：按本节调用链完成对应处理
#   - `build_retriever() -> Retriever`：输入为签名中的参数；输出为 `Retriever`。用途：加载语料 -> 清洗切分 -> 倒排入库,返回就绪的检索器。
#   - `build_llm() -> ChatOpenAI`：输入为签名中的参数；输出为 `ChatOpenAI`。用途：装配 DeepSeek 客户端(OpenAI 兼容协议),配置全部来自环境变量。
#   - `build_prompt(question: str, hits: list[tuple[Chunk, int]]) -> str`：输入为签名中的参数；输出为 `str`。用途：把检索片段编号后拼进提示词,约束模型只依据资料作答。
#   - `rag_ask(retriever: Retriever, question: str) -> str`：输入为签名中的参数；输出为 `str`。用途：RAG 问答:检索 -> 拼提示词 -> 调模型(或剧本) -> 返回回答。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Chunk`：承载本节状态/数据；重点方法：见类定义。
#   - `Retriever`：承载本节状态/数据；重点方法：add_chunks, search。
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import os
import re
import sys
from collections import Counter, defaultdict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

MOCK = os.environ.get("MOCK_LLM") == "1"  # 离线演示模式

if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[黑糖资料室] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地离线演示可设 MOCK_LLM=1,用剧本模拟模型回答)")
    sys.exit(0)

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


def build_retriever() -> Retriever:
    """加载语料 -> 清洗切分 -> 倒排入库,返回就绪的检索器。"""
    retriever = Retriever()
    for title, content in load_docs():
        retriever.add_chunks(chunk_document(title, content))
    return retriever


def build_llm() -> ChatOpenAI:
    """装配 DeepSeek 客户端(OpenAI 兼容协议),配置全部来自环境变量。"""
    # TODO: 返回 ChatOpenAI 客户端,四要素全部从环境变量读取
    # 提示: model=os.environ.get("MODEL_NAME", "deepseek-v4-pro");api_key 与 base_url 同样从环境变量取;temperature=0 关随机性
    raise NotImplementedError("t71-rag-pipeline-s4 尚未实现:请按 TODO 提示装配 build_llm")


SYSTEM_PROMPT = "你是「黑糖资料室」知识库助手。只依据提供的资料回答,并标注引用来源;资料没有的就直说不知道。"


def build_prompt(question: str, hits: list[tuple[Chunk, int]]) -> str:
    """把检索片段编号后拼进提示词,约束模型只依据资料作答。"""
    parts = [f"[{i}]《{chunk.title}》: {chunk.text}" for i, (chunk, _) in enumerate(hits, 1)]
    return "以下是知识库资料:\n" + "\n".join(parts) + f"\n\n问题:{question}\n请结合资料回答,并注明 [i] 来源。"


def rag_ask(retriever: Retriever, question: str) -> str:
    """RAG 问答:检索 -> 拼提示词 -> 调模型(或剧本) -> 返回回答。"""
    # TODO: 召回片段并拼提示词;MOCK 分支按命中片段标题返回剧本回答,真实分支调用模型
    # 提示: retriever.search(question) 与 build_prompt(question, hits);MOCK 时拼接 sorted({c.title for c, _ in hits}) 成回答;否则 build_llm().invoke([SystemMessage(...), HumanMessage(...)])
    raise NotImplementedError("t71-rag-pipeline-s4 尚未实现:请按 TODO 提示完成 rag_ask 问答链路")


def main() -> None:
    retriever = build_retriever()
    question = "黑糖资料室的架构分为哪几层?"
    answer = rag_ask(retriever, question)
    print(f"\n[回答] {answer}")


if __name__ == "__main__":
    main()
