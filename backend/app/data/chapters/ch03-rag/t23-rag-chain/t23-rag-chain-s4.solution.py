"""黑糖资料室第 4 步:引用溯源 —— 编号注入 prompt + 程序抓回核对,让每句回答有据可查。"""
import os, re, sys, zlib

import numpy as np

CHUNK_SIZE, CHUNK_OVERLAP = 60, 15
EMBED_DIM, TOP_K = 512, 3
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")

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
    """第 1 步成果:参考资料切块,出处元数据随切片走。"""
    chunks, step = [], max(chunk_size - overlap, 1)
    for doc in documents:
        text = doc["content"]
        for start in range(0, len(text), step):
            piece = text[start:start + chunk_size]
            chunks.append({"text": piece, "source": doc["source"], "doc_id": doc["doc_id"]})
    return chunks


class LocalEmbedder:  # 第 2 步成果:单字/双字 token 经 crc32 哈希到固定维度
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
        q = self.embedder.embed(query)
        scores = self.matrix @ q
        order = np.argsort(scores)[::-1][:top_k]
        return [(self.chunks[i], float(scores[i])) for i in order]


def build_context(results):
    """检索结果编号注入:【n】出处 + 正文,编号就是模型的「可引之物」。"""
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
            return "【MOCK】异常过滤策略专克基础指南深厚的对手[1],习这份方案者须忘却固定模板、只记设计思路[2]。"
        resp = self.client.chat.completions.create(
            model=MODEL_NAME, temperature=0.3,
            messages=[{"role": "user", "content": prompt}])
        return resp.choices[0].message.content


def extract_citations(answer, results):
    """抓出答案中的 [n] 引用,映射回真实出处;编号越界即「引用幻觉」。"""
    valid, phantom = [], []
    for n in sorted({int(x) for x in re.findall(r"\[(\d+)\]", answer)}):
        if 1 <= n <= len(results):
            valid.append(results[n - 1][0]["source"])
        else:
            phantom.append(n)  # 模型引用了根本不存在的片段编号
    return valid, phantom


def rag_answer(store, llm, question):
    """RAG 主链:检索 → 编号上下文 → 生成 → 引用校验。"""
    results = store.search(question)
    prompt = PROMPT_TEMPLATE.format(context=build_context(results), question=question)
    answer = llm.chat(prompt)
    valid, phantom = extract_citations(answer, results)
    return {"answer": answer, "sources": valid, "phantom": phantom}


def main():
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)
    store = VectorStore(LocalEmbedder())
    store.add(chunk_documents(DOCUMENTS))
    question = "重排设计指南的异常过滤策略有什么用?"
    result = rag_answer(store, DeepSeekLLM(), question)
    print(f"问:{question}\n答:{result['answer']}")
    print("引用来源:" + ("、".join(result["sources"]) if result["sources"] else "(答案未标注)"))
    if result["phantom"]:
        print(f"注意:答案引用了不存在的编号 {result['phantom']}(引用幻觉)")


if __name__ == "__main__":
    main()
