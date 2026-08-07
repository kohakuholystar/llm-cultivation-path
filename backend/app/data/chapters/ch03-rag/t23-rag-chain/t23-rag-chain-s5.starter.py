"""藏经阁第 5 步:幻觉兜底与管线封装 —— 藏经阁竣工。"""
import os, re, sys, zlib

import numpy as np

CHUNK_SIZE, CHUNK_OVERLAP = 60, 15
EMBED_DIM, TOP_K = 512, 3
SCORE_THRESHOLD = 0.19  # 相似度阈值:实测阁内提问得分 ≥0.20、阁外噪声 ≤0.18,取中间线
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
FALLBACK_MESSAGE = "小僧翻遍藏经阁,未找到与香客所问相关的秘籍记载,不敢妄言。请换个问法,或改问本阁收藏的武功门类。"

DOCUMENTS = [
    {"doc_id": "yjj", "source": "《易筋经·卷一》", "content": "易筋经乃少林镇寺之宝,讲究以意导气、以气运力。修习者需每日寅时起身,面东而立,先行吐纳三十六次,再依图谱摆出十二式桩架。初学者切忌贪快,桩架不正则气行偏差,轻则筋骨酸痛,重则伤及经络。经中明言:宁可十日不进阶,不可一日错行功。"},
    {"doc_id": "jy", "source": "《九阳真经·总纲》", "content": "九阳真经重在内力生生不息。其总纲云:他强由他强,清风拂山岗。修习九阳神功者,内力自行周天运转,寒暑不侵,百毒难伤。然此功进境极缓,非有大毅力者不能成。觉远大师于华山之巅口述此经,张君宝与郭襄各得一部分,后衍化为武当、峨眉两派内功根基。"},
    {"doc_id": "dg", "source": "《独孤九剑·剑理篇》", "content": "独孤九剑共九式,破尽天下武功。其核心剑理只有四个字:料敌机先。风清扬传令狐冲时言:剑招是死的,人是活的,无招胜有招。破剑式用以破解各派剑法,破刀式克制单刀双刀,破气式则专克内功深厚的对手。习此剑者须忘却固定招式,只记剑意。"},
    {"doc_id": "qk", "source": "《乾坤大挪移·心法》", "content": "乾坤大挪移为明教镇教神功,共分七层。其要义在于激发人体潜力、挪移乾坤二气。第一层需七年苦修,第二层加倍,层层递进。张无忌因身具九阳神功,内力深厚,方能在密道中速成。此功最忌根基不牢而强行冲关,历代教主多有因此殒命者。"},
]

PROMPT_TEMPLATE = """你是藏经阁的守阁僧人,只能依据下列编号片段回答,并在每个事实后用 [编号] 标注出处。
【秘籍片段】
{context}
【香客提问】
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
            return "【MOCK】守阁僧人答:修习须循序渐进、桩架端正,切忌贪快[1]。(离线假回复)"
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
    """藏经阁问答管线:检索 → 阈值过滤 → 生成 → 引用校验。"""

    def __init__(self, documents):
        self.store = VectorStore(LocalEmbedder())
        self.store.add(chunk_documents(documents))
        self.llm = DeepSeekLLM()

    def retrieve(self, question, top_k=TOP_K):
        """top-k 结果再过相似度阈值:低于 SCORE_THRESHOLD 的一律丢弃。"""
        # TODO: 检索结果再过相似度阈值,只保留高分命中
        # 提示: return [(c, s) for c, s in self.store.search(question, top_k) if s >= SCORE_THRESHOLD]
        raise NotImplementedError("t23-s5 尚未实现:请按 TODO 提示完成 retrieve 阈值过滤")

    def answer(self, question):
        hits = self.retrieve(question)
        # TODO: 命中与兜底两个分支:无命中直接拒答,有命中走生成+引用校验
        # 提示: if not hits: return {"answer": FALLBACK_MESSAGE, "sources": [], "grounded": False};否则 prompt = PROMPT_TEMPLATE.format(context=build_context(hits), question=question) → text = self.llm.chat(prompt) → valid, phantom = extract_citations(text, hits),返回 {"answer": text, "sources": valid, "phantom": phantom, "grounded": True}
        raise NotImplementedError("t23-s5 尚未实现:请按 TODO 提示完成 answer 兜底与生成")


def main():
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("MOCK_LLM"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)
    rag = CangjingRAG(DOCUMENTS)
    for q in ["初学者练易筋经要注意什么?", "藏经阁里有没有意大利面的做法?"]:
        r = rag.answer(q)
        tag = "、".join(r["sources"]) if r["grounded"] else "兜底拒答,未调用大模型"
        print(f"问:{q}\n答:{r['answer']}\n[{tag}]\n")


if __name__ == "__main__":
    main()
