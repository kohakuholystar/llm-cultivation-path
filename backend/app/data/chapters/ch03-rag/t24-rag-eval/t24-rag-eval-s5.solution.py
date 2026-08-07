"""藏经阁收官 · 第五步:忠实度评估与 Bad Case 分析——给藏经阁出一份体检报告。"""
import math, os, re, sys
from collections import Counter

MOCK = os.environ.get("MOCK_LLM") == "1"          # 离线演示开关(第二步成果,压缩复用)
API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
if not MOCK and not API_KEY:  # 无 key 时优雅退出
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
    han = re.findall(r"[一-鿿]", text)  # 纯中文语料:取汉字做相邻两字 bigram
    return ["".join(han[i:i + 2]) for i in range(len(han) - 1)]


class TfidfRetriever:  # 纯 Python TF-IDF 检索器(前三步沿用)
    def __init__(self, docs):
        self.docs = docs
        self.tf = [Counter(tokenize(d["text"])) for d in docs]
        df = Counter(t for counts in self.tf for t in counts)
        self.idf = {t: math.log((len(docs) + 1) / (c + 1)) + 1 for t, c in df.items()}

    def search(self, query, k=3):
        scored = [(d, sum(c.get(t, 0) * self.idf.get(t, 0.0) for t in tokenize(query)))
                  for d, c in zip(self.docs, self.tf)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


TEST_SET = [
    {"question": "如何修炼内功?", "relevant": ["d1"]},
    {"question": "弟子受伤流血该用什么药?", "relevant": ["d5"]},
    {"question": "剑法的最高境界是什么?", "relevant": ["d3"]},
    {"question": "能把经书带回厢房研读吗?", "relevant": ["d6"]},
    {"question": "拳法与剑法孰强孰弱?", "relevant": []},  # 观点题,库中无标准答案
    {"question": "禅师的床底下藏着什么?", "relevant": []},]  # 库外问题,幻觉标本


def chat(prompt):  # 调 DeepSeek;异常返回带标记文本,评估流程不中断
    try:
        resp = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0)
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        return f"[LLM 调用失败] {exc}"


MOCK_REWRITES = {  # 离线演示的固定改写表;"剑法"一题改写故意不给力,留作 bad case;Q1 单查已命中,无需改写
    "弟子受伤流血该用什么药?": ["止血疗伤用什么药", "金疮药如何配制", "外伤出血怎么包扎"],
    "剑法的最高境界是什么?": ["剑术的真谛是什么", "如何做到料敌机先", "剑理的核心思想"],
    "能把经书带回厢房研读吗?": ["典籍借阅有什么规矩", "把经书带出寺外会怎样", "借阅手谕怎么申请"],
}


def multi_search(retriever, question, k=2):
    """第四步成果:MultiQuery 改写 + max-score 融合,零分文档不进并集。"""
    rewrites = MOCK_REWRITES.get(question, []) if MOCK else chat(
        f"把下面的问题改写成 3 个不同问法,每行一个,不要编号:\n{question}").splitlines()
    best = {}
    for q in [question] + [ln.strip() for ln in rewrites if ln.strip()]:
        for doc, score in retriever.search(q, k=k):
            if score > 0 and score > best.get(doc["id"], (0.0,))[0]:
                best[doc["id"]] = (score, doc)
    return [(doc, score) for score, doc in  # 同篇文档只留各路中的最高分
            sorted(best.values(), key=lambda item: item[0], reverse=True)[:k]]


def generate_answer(question, hits):
    """第二步成果:资料拼进 prompt;MOCK 下检索为空就凭"记忆"瞎答(幻觉标本)。"""
    if MOCK:
        return (f"根据藏经阁记载:{hits[0][0]['text']}" if hits else
                "据我所知,这与失传的易筋经有关,藏经阁每日戌时开放借阅。")
    context = "\n".join(d["text"] for d, _ in hits)
    return chat(f"基于以下资料回答,资料不足就说“根据现有资料无法回答”。\n资料:\n{context}\n问题:{question}")


def check_faithfulness(answer, hits):
    """忠实度:答案须被检索资料支撑。MOCK 用前缀启发式;真实环境让 LLM 当裁判。"""
    if MOCK:
        return answer.startswith("根据藏经阁记载:")  # 引用原文判忠实,凭空口述判幻觉
    context = "\n".join(d["text"] for d, _ in hits) or "(检索无资料)"
    prompt = f"资料:\n{context}\n答案:{answer}\n答案每句都有资料依据,或明确拒答吗?只回“忠实”或“幻觉”。"
    return "忠实" in chat(prompt)


def diagnose(relevant, hit_ids, faithful):  # 失败分类学(按优先级归类):不同病灶,不同药方
    if relevant and not set(hit_ids) & set(relevant):
        return "检索失败", "改写词与文档用词仍零重叠——该上向量检索了(见 t21)"
    if not relevant and hit_ids:
        return "误检", "检出了无关文档——加相关性阈值或重排序(见 t22)"
    if not faithful:
        return "生成幻觉", "检索为空时应强制拒答,而不是凭记忆硬答"
    return ("通过", "") if relevant else ("正确拒绝", "")


if __name__ == "__main__":
    retriever = TfidfRetriever(CORPUS)
    print(f"=== 藏经阁质量体检报告(MOCK={MOCK})===")
    bad_cases = []
    for item in TEST_SET:
        hits = multi_search(retriever, item["question"], k=2)
        answer = generate_answer(item["question"], hits)
        verdict, fix = diagnose(item["relevant"], [d["id"] for d, _ in hits],
                                check_faithfulness(answer, hits))
        print(f"[{verdict}] {item['question']} → {answer[:26]}")
        if verdict not in ("通过", "正确拒绝"):
            bad_cases.append((item["question"], verdict, fix))
    print(f"\n=== Bad Case 分析表:{len(bad_cases)} 条 / 共 {len(TEST_SET)} 题 ===")
    for question, verdict, fix in bad_cases:
        print(f"  {verdict} | {question} | 药方:{fix}")
