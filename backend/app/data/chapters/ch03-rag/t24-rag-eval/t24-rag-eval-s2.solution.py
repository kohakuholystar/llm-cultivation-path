"""藏经阁收官 · 第二步:接入 DeepSeek 生成端(检索 → 拼 prompt → 回答)。"""
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


def generate_answer(question, hits):
    """检索+生成:把 top 文档拼进 prompt,要求资料不足时如实拒答。"""
    if MOCK:  # 检索得分 0 → 故意凭"记忆"瞎答,制造幻觉标本
        if not hits or hits[0][1] == 0:
            return "据我所知,这与失传的易筋经有关,藏经阁每日戌时开放借阅。"
        return f"根据藏经阁记载:{hits[0][0]['text']}"
    context = "\n".join(d["text"] for d, _ in hits)
    prompt = (f"基于以下资料回答问题,资料不足就说“根据现有资料无法回答”。\n"
              f"资料:\n{context}\n问题:{question}")
    return chat(prompt)


if __name__ == "__main__":
    retriever = TfidfRetriever(CORPUS)
    print(f"=== 藏经阁问答(MODEL={MODEL}, MOCK={MOCK})===")
    for item in TEST_SET[:3]:
        hits = retriever.search(item["question"], k=2)
        answer = generate_answer(item["question"], hits)
        print(f"问:{item['question']}\n答:{answer}\n")
