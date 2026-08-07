"""藏经阁第 3 步:RAG 链组装 —— 本地检索 + DeepSeek 生成。

问题 → 向量检索 top-k → 片段拼进 prompt → deepseek-v4-pro 基于证据作答。
设置 MOCK_LLM=1 可在无网环境用假回复演示整条链路。
"""
import os
import sys
import zlib

import numpy as np

CHUNK_SIZE, CHUNK_OVERLAP = 60, 15
EMBED_DIM, TOP_K = 512, 3
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")

# 藏经阁秘籍总目(第 1 步登记的语料,内联自带保证单文件可跑)
DOCUMENTS = [
    {"doc_id": "yjj", "source": "《易筋经·卷一》", "content": "易筋经乃少林镇寺之宝,讲究以意导气、以气运力。修习者需每日寅时起身,面东而立,先行吐纳三十六次,再依图谱摆出十二式桩架。初学者切忌贪快,桩架不正则气行偏差,轻则筋骨酸痛,重则伤及经络。经中明言:宁可十日不进阶,不可一日错行功。"},
    {"doc_id": "jy", "source": "《九阳真经·总纲》", "content": "九阳真经重在内力生生不息。其总纲云:他强由他强,清风拂山岗。修习九阳神功者,内力自行周天运转,寒暑不侵,百毒难伤。然此功进境极缓,非有大毅力者不能成。觉远大师于华山之巅口述此经,张君宝与郭襄各得一部分,后衍化为武当、峨眉两派内功根基。"},
    {"doc_id": "dg", "source": "《独孤九剑·剑理篇》", "content": "独孤九剑共九式,破尽天下武功。其核心剑理只有四个字:料敌机先。风清扬传令狐冲时言:剑招是死的,人是活的,无招胜有招。破剑式用以破解各派剑法,破刀式克制单刀双刀,破气式则专克内功深厚的对手。习此剑者须忘却固定招式,只记剑意。"},
    {"doc_id": "qk", "source": "《乾坤大挪移·心法》", "content": "乾坤大挪移为明教镇教神功,共分七层。其要义在于激发人体潜力、挪移乾坤二气。第一层需七年苦修,第二层加倍,层层递进。张无忌因身具九阳神功,内力深厚,方能在密道中速成。此功最忌根基不牢而强行冲关,历代教主多有因此殒命者。"},
]

PROMPT_TEMPLATE = """你是藏经阁的守阁僧人,只依据下列秘籍片段回答香客提问,不得编造片段之外的内容。

【秘籍片段】
{context}

【香客提问】
{question}

请用中文简洁作答:"""


def chunk_documents(documents, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """第 1 步成果:秘籍切块,出处元数据随切片走。"""
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
        if self.mock:
            return "【MOCK】守阁僧人依据秘籍片段给出回答(真实运行时此处为 deepseek-v4-pro 的生成结果)。"
        resp = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # 低温让回答更忠实于证据,减少自由发挥
        )
        return resp.choices[0].message.content


def rag_answer(store, llm, question):
    """RAG 主链:检索 → 拼上下文 → 生成,三段一次走完。"""
    results = store.search(question)
    context = build_context(results)
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)
    return llm.chat(prompt)


def main():
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)  # 无 Key 优雅退出,不抛 traceback
    store = VectorStore(LocalEmbedder())
    store.add(chunk_documents(DOCUMENTS))
    question = "初学者练易筋经要注意什么?"
    print(f"问:{question}")
    print("答:" + rag_answer(store, DeepSeekLLM(), question))


if __name__ == "__main__":
    main()
