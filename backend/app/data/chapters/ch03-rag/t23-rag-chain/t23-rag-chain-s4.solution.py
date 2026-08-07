"""藏经阁第 4 步:引用溯源 —— 编号注入 prompt + 程序抓回核对,让每句回答有据可查。"""
import os, re, sys, zlib

import numpy as np

CHUNK_SIZE, CHUNK_OVERLAP = 60, 15
EMBED_DIM, TOP_K = 512, 3
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")

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
            return "【MOCK】破气式专克内功深厚的对手[1],习此剑者须忘却固定招式、只记剑意[2]。"
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
    question = "独孤九剑的破气式有什么用?"
    result = rag_answer(store, DeepSeekLLM(), question)
    print(f"问:{question}\n答:{result['answer']}")
    print("引用来源:" + ("、".join(result["sources"]) if result["sources"] else "(答案未标注)"))
    if result["phantom"]:
        print(f"注意:答案引用了不存在的编号 {result['phantom']}(引用幻觉)")


if __name__ == "__main__":
    main()
