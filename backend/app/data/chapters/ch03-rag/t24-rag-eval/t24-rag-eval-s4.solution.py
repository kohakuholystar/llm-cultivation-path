"""藏经阁收官 · 第四步:MultiQuery 查询扩展——一个问法找不到,就换几个问法再找。"""
import math
import os
import re
import sys
from collections import Counter

# ---------- LLM 接入:配置一律走环境变量,绝不硬编码 key ----------
MOCK = os.environ.get("MOCK_LLM") == "1"                      # 离线演示开关
API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
if not MOCK and not API_KEY:  # 无 key 时优雅退出,不给学习者看 traceback
    print("请先在右上角 AI 配置填入 DeepSeek API Key")
    sys.exit(0)
from openai import OpenAI
client = None if MOCK else OpenAI(api_key=API_KEY, base_url=BASE_URL)

CORPUS = [
    {"id": "d1", "text": "吐纳心法:内功根基在于吐纳,每日卯时面东打坐,气沉丹田,调匀呼吸,百日方可筑基。"},
    {"id": "d3", "text": "剑谱总纲:剑之道,快不如巧,巧不如拙,大巧若拙,无招胜有招。"},
    {"id": "d4", "text": "拳经:拳法力从地起,腰马合一,劲达四梢,练拳不练功,到老一场空。"},
    {"id": "d5", "text": "药典:金疮药以三七、血竭为主,辅以冰片研末,外敷可止血生肌。"},
    {"id": "d6", "text": "寺规:藏经阁典籍不得带出寺外,借阅需长老手谕,违者罚面壁三月。"},
]


def tokenize(text):
    """切词:英文数字按词,中文按相邻两字 bigram(无分词库时的零依赖折中)。"""
    words = re.findall(r"[a-z0-9]+", text.lower())
    han = re.findall(r"[一-鿿]", text)
    return words + ["".join(han[i:i + 2]) for i in range(len(han) - 1)]


class TfidfRetriever:
    """纯 Python TF-IDF 检索器(第一步成果,压缩复用)。"""
    def __init__(self, docs):
        self.docs = docs
        self.tf = [Counter(tokenize(d["text"])) for d in docs]
        df = Counter(t for counts in self.tf for t in counts)
        self.idf = {t: math.log((len(docs) + 1) / (c + 1)) + 1 for t, c in df.items()}

    def search(self, query, k=3):
        scored = [(doc, sum(counts.get(t, 0) * self.idf.get(t, 0.0) for t in tokenize(query)))
                  for doc, counts in zip(self.docs, self.tf)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


TEST_SET = [
    {"question": "如何修炼内功?", "relevant": ["d1"]},
    {"question": "弟子受伤流血该用什么药?", "relevant": ["d5"]},
    {"question": "剑法的最高境界是什么?", "relevant": ["d3"]},
    {"question": "能把经书带回厢房研读吗?", "relevant": ["d6"]},
    {"question": "拳法与剑法孰强孰弱?", "relevant": []},    # 观点题,库中无标准答案
    {"question": "禅师的床底下藏着什么?", "relevant": []},  # 库外问题,留作幻觉标本
]


def chat(prompt):
    """调 DeepSeek 对话接口,返回文本;异常不抛出,返回带标记的错误说明。"""
    try:
        resp = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0)
        return resp.choices[0].message.content.strip()
    except Exception as exc:  # 网络抖动/限流不应中断评估流程
        return f"[LLM 调用失败] {exc}"


MOCK_REWRITES = {  # 离线演示的固定改写表;"剑法"一题改写故意不给力,留作 bad case;Q1 单查已命中,无需改写
    "弟子受伤流血该用什么药?": ["止血疗伤用什么药", "金疮药如何配制", "外伤出血怎么包扎"],
    "剑法的最高境界是什么?": ["剑术的真谛是什么", "如何做到料敌机先", "剑理的核心思想"],
    "能把经书带回厢房研读吗?": ["典籍借阅有什么规矩", "把经书带出寺外会怎样", "借阅手谕怎么申请"],
}


def expand_query(question, n=3):
    """MultiQuery:让 LLM 把原问题改写成 n 个不同问法;原问题始终保留作锚。"""
    if MOCK:
        rewrites = MOCK_REWRITES.get(question, [])  # 离线查表;库外题不改写
    else:
        prompt = f"把下面的问题改写成 {n} 个不同问法,每行一个,不要编号:\n{question}"
        rewrites = [ln.strip() for ln in chat(prompt).splitlines() if ln.strip()]
    return [question] + [r for r in rewrites if r != question]


def multi_search(retriever, question, k=2):
    """多路检索 + max-score 融合:每篇文档取各路查询中的最高分,零分不进并集。"""
    best = {}
    for q in expand_query(question):
        for doc, score in retriever.search(q, k=k):
            if score > 0 and score > best.get(doc["id"], (0.0,))[0]:
                best[doc["id"]] = (score, doc)  # 同篇文档只保留最高分
    fused = sorted(best.values(), key=lambda item: item[0], reverse=True)[:k]
    return [(doc, score) for score, doc in fused]


if __name__ == "__main__":
    retriever = TfidfRetriever(CORPUS)
    print(f"=== MultiQuery 召回对比(MODEL={MODEL}, MOCK={MOCK})===")
    singles, multis = [], []
    for item in TEST_SET:
        if not item["relevant"]:
            continue  # 库外题没有召回率,留给第五步做忠实度分析
        s_ids = [d["id"] for d, sc in retriever.search(item["question"], k=2) if sc > 0]
        m_ids = [d["id"] for d, _ in multi_search(retriever, item["question"], k=2)]
        s_rec = len(set(s_ids) & set(item["relevant"])) / len(item["relevant"])
        m_rec = len(set(m_ids) & set(item["relevant"])) / len(item["relevant"])
        singles.append(s_rec)
        multis.append(m_rec)
        print(f"{item['question']} 单查 {s_rec:.2f} → 多查 {m_rec:.2f}")
    print(f"\n平均 Recall@2:单查询 {sum(singles)/len(singles):.2f} → 多查询 {sum(multis)/len(multis):.2f}")
