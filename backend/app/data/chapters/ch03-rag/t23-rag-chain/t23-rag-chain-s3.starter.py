"""黑糖资料室第 3 步:RAG 链组装 —— 本地检索 + DeepSeek 生成。

问题 → 向量检索 top-k → 片段拼进 prompt → deepseek-v4-pro 基于证据作答。
设置 MOCK_LLM=1 可在无网环境用假回复演示整条链路。
"""
# 学习契约
# 目标：完成 t23-rag-chain-s3 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 4 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：chunk_documents(documents, chunk_size, overlap) -> 未标注; build_context(results) -> 未标注; rag_answer(store, llm, question) -> 未标注; main() -> 未标注。
# 技术栈：os, sys, zlib, numpy；前置条件：在右上角 AI 配置填入自己的 DeepSeek API Key。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
import os
import sys
import zlib

import numpy as np

CHUNK_SIZE, CHUNK_OVERLAP = 60, 15
EMBED_DIM, TOP_K = 512, 3
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")

# 黑糖资料室参考资料总目(第 1 步登记的语料,内联自带保证单文件可跑)
DOCUMENTS = [
    {"doc_id": "yjj", "source": "《文档切分指南·第一章》", "content": "文档切分指南是资料组的核心文档。处理前先统一编码与换行,再按标题、段落和长度边界切分。初学者不要只追求切块数量:片段过短会丢失上下文,片段过长会降低检索精度。每次调整参数后都应保存样例并复查引用是否仍能回到原文。"},
    {"doc_id": "jy", "source": "《检索基础指南·总纲》", "content": "检索基础指南强调召回稳定性。查询进入系统后先规范化文本,再从索引中取得候选片段。候选不足时应记录未命中的查询,而不是让生成模型补写事实。资料组、开发组和测试组分别维护数据、实现与回归样例。"},
    {"doc_id": "dg", "source": "《重排设计指南》", "content": "重排设计指南介绍如何把更相关的候选放到前面。先保留召回阶段的候选集,再结合关键词覆盖、来源质量和位置特征计算分数。同分结果使用稳定的文档编号排序,避免多次运行顺序漂移。"},
    {"doc_id": "qk", "source": "《黑糖资料室·检索设计》", "content": "黑糖资料室采用分层检索设计,共分数据加载、文本切分、候选召回、结果重排与引用生成五层。其要义是让回答始终能回到原始资料。第一层负责统一格式,第二层保留上下文边界,后续层逐步提高相关性。若跳过数据质量检查直接生成回答,结果容易失去可靠来源。"},
]

PROMPT_TEMPLATE = """你是黑糖资料室的资料管理员,只依据下列操作指南片段回答用户提问,不得编造片段之外的内容。

【操作指南片段】
{context}

【用户提问】
{question}

请用中文简洁作答:"""


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
    """把检索结果拼成上下文文本,每段标注出处。"""
    parts = [f"【片段】{chunk['source']}:{chunk['text']}" for chunk, _ in results]
    return "\n\n".join(parts)


class DeepSeekLLM:
    """DeepSeek 对话封装;MOCK_LLM=1 时返回假回复,无网也能演示链路。"""

    def __init__(self):
        self.mock = bool(os.environ.get("MOCK_LLM"))
        self.client = None
        if not self.mock:
            from openai import OpenAI  # DeepSeek 兼容 OpenAI 协议,换 base_url 即用
            self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=BASE_URL)

    def chat(self, prompt):
        # TODO: 区分 mock 与真实两分支完成 LLM 调用
        # 提示: mock 时直接返回一条中文假回复;否则 resp = self.client.chat.completions.create(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}], temperature=0.3),返回 resp.choices[0].message.content
        raise NotImplementedError("t23-s3 尚未实现:请按 TODO 提示完成 chat 调用")


def rag_answer(store, llm, question):
    """RAG 主链:检索 → 拼上下文 → 生成,三段一次走完。"""
    # TODO: 串起检索、拼上下文、构造 prompt 并交给 LLM 生成
    # 提示: results = store.search(question);context = build_context(results);prompt = PROMPT_TEMPLATE.format(context=context, question=question);返回 llm.chat(prompt)
    raise NotImplementedError("t23-s3 尚未实现:请按 TODO 提示完成 rag_answer 主链")


def main():
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)  # 无 Key 优雅退出,不抛 traceback
    store = VectorStore(LocalEmbedder())
    store.add(chunk_documents(DOCUMENTS))
    question = "初学者练文档切分指南要注意什么?"
    print(f"问:{question}")
    print("答:" + rag_answer(store, DeepSeekLLM(), question))


if __name__ == "__main__":
    main()
