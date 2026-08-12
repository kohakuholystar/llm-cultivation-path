"""黑糖资料室第 5 步:幻觉兜底与管线封装 —— 黑糖资料室竣工。"""
import os, re, sys, zlib

import numpy as np

CHUNK_SIZE, CHUNK_OVERLAP = 60, 15
EMBED_DIM, TOP_K = 512, 3
SCORE_THRESHOLD = 0.19  # 相似度阈值:实测库内提问得分 ≥0.20、库外噪声 ≤0.18,取中间线
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
FALLBACK_MESSAGE = "黑糖资料室暂未找到与当前问题相关的操作指南。请换个问法,或改问资料库已收录的技术主题。"

DOCUMENTS = [
    {"doc_id": "yjj", "source": "《文档切分指南·第一章》", "content": "文档切分指南是资料组的核心文档。处理前先统一编码与换行,再按标题、段落和长度边界切分。初学者不要只追求切块数量:片段过短会丢失上下文,片段过长会降低检索精度。每次调整参数后都应保存样例并复查引用是否仍能回到原文。"},
    {"doc_id": "jy", "source": "《检索基础指南·总纲》", "content": "检索基础指南强调召回稳定性。查询进入系统后先规范化文本,再从索引中取得候选片段。候选不足时应记录未命中的查询,而不是让生成模型补写事实。资料组、开发组和测试组分别维护数据、实现与回归样例。"},
    {"doc_id": "dg", "source": "《重排设计指南》", "content": "重排设计指南介绍如何把更相关的候选放到前面。先保留召回阶段的候选集,再结合关键词覆盖、来源质量和位置特征计算分数。同分结果使用稳定的文档编号排序,避免多次运行顺序漂移。"},
    {"doc_id": "qk", "source": "《黑糖资料室·检索设计》", "content": "黑糖资料室采用分层检索设计,共分数据加载、文本切分、候选召回、结果重排与引用生成五层。其要义是让回答始终能回到原始资料。第一层负责统一格式,第二层保留上下文边界,后续层逐步提高相关性。若跳过数据质量检查直接生成回答,结果容易失去可靠来源。"},
]

PROMPT_TEMPLATE = """你是黑糖资料室的资料管理员,只能依据下列编号片段回答,并在每个事实后用 [编号] 标注出处。
【操作指南片段】
{context}
【用户提问】
{question}
片段中没有的内容要明说不知道,禁止编造。回答:"""


def chunk_documents(documents, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks, step = [], max(chunk_size - overlap, 1)
    for doc in documents:
        for start in range(0, len(doc["content"]), step):
            chunks.append({"text": doc["content"][start:start + chunk_size],
                           "source": doc["source"], "doc_id": doc["doc_id"]})
    return chunks


class LocalEmbedder:  # 第 2 步成果:单/双字 token 哈希 embedding
    def __init__(self, dim=EMBED_DIM, ngram=(1, 2)):
        self.dim, self.ngram = dim, ngram

    def embed(self, text):
        vec = np.zeros(self.dim, dtype=np.float32)
        for n in self.ngram:
            for i in range(len(text) - n + 1):
                vec[zlib.crc32(text[i:i + n].encode("utf-8")) % self.dim] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def embed_all(self, texts): return np.stack([self.embed(t) for t in texts])


class VectorStore:  # 第 2 步成果:余弦相似度 top-k 检索
    def __init__(self, embedder):
        self.embedder, self.chunks, self.matrix = embedder, [], None

    def add(self, chunks):
        self.chunks = chunks
        self.matrix = self.embedder.embed_all([c["text"] for c in chunks])

    def search(self, query, top_k=TOP_K):
        scores = self.matrix @ self.embedder.embed(query)
        return [(self.chunks[i], float(scores[i])) for i in np.argsort(scores)[::-1][:top_k]]


def build_context(results):
    return "\n".join(f"【{i}】{c['source']}:{c['text']}" for i, (c, _) in enumerate(results, 1))


class DeepSeekLLM:  # MOCK_LLM=1 时返回带 [1] 引用的假回复
    def __init__(self):
        self.mock = bool(os.environ.get("MOCK_LLM"))
        self.client = None
        if not self.mock:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=BASE_URL)

    def chat(self, prompt):
        if self.mock:
            return "【MOCK】资料管理员答:切分时需保留上下文边界,并在调整参数后复查引用[1]。(离线假回复)"
        resp = self.client.chat.completions.create(
            model=MODEL_NAME, temperature=0.3,
            messages=[{"role": "user", "content": prompt}])
        return resp.choices[0].message.content


def extract_citations(answer, results):
    """抓出答案中的 [n],映射回出处;编号越界即引用幻觉。"""
    valid, phantom = [], []
    for n in sorted({int(x) for x in re.findall(r"\[(\d+)\]", answer)}):
        if 1 <= n <= len(results):
            valid.append(results[n - 1][0]["source"])
        else: phantom.append(n)
    return valid, phantom


class CangjingRAG:
    """黑糖资料室问答管线:检索 → 阈值过滤 → 生成 → 引用校验。"""

    def __init__(self, documents):
        self.store = VectorStore(LocalEmbedder())
        self.store.add(chunk_documents(documents))
        self.llm = DeepSeekLLM()

    def retrieve(self, question, top_k=TOP_K):
        """top-k 结果再过相似度阈值:低于 SCORE_THRESHOLD 的一律丢弃。"""
        return [(c, s) for c, s in self.store.search(question, top_k) if s >= SCORE_THRESHOLD]

    def answer(self, question):
        hits = self.retrieve(question)
        if not hits:  # 资料库无相关记录:不调用 LLM,直接兜底——拒答优于错答
            return {"answer": FALLBACK_MESSAGE, "sources": [], "grounded": False}
        prompt = PROMPT_TEMPLATE.format(context=build_context(hits), question=question)
        text = self.llm.chat(prompt)
        valid, phantom = extract_citations(text, hits)
        return {"answer": text, "sources": valid, "phantom": phantom, "grounded": True}


def main():
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)
    rag = CangjingRAG(DOCUMENTS)
    for q in ["初学者练文档切分指南要注意什么?", "黑糖资料室里有没有意大利面的做法?"]:
        r = rag.answer(q)
        tag = "、".join(r["sources"]) if r["grounded"] else "兜底拒答,未调用大模型"
        print(f"问:{q}\n答:{r['answer']}\n[{tag}]\n")


if __name__ == "__main__":
    main()
