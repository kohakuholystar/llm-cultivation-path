"""黑糖资料室收官 · 第二步:接入 DeepSeek 生成端(检索 → 拼 prompt → 回答)。"""
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
    {"id": "d1", "text": "数据清洗方法:先统一编码与字段格式,再处理重复值和缺失值,最后写入缓存并保存质量报告。"},
    {"id": "d3", "text": "输出模板指南:先明确字段契约,再减少无效规则,并用固定样例验证输出稳定性。"},
    {"id": "d4", "text": "设计规范:版式需要统一间距、字号与颜色层级,并通过样例检查一致性。"},
    {"id": "d5", "text": "应急手册:轻微外伤先清洁并止血,必要时及时联系校医或专业人员。"},
    {"id": "d6", "text": "借阅规范:黑糖资料室的受限资料不得外传,借阅需获得管理员授权并记录用途。"},
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
    {"question": "如何学习基础指南?", "relevant": ["d1"]},
    {"question": "成员轻微外伤应该如何处理?", "relevant": ["d5"]},
    {"question": "创作方法的最高学习阶段是什么?", "relevant": ["d3"]},
    {"question": "能把受限文档带离资料室吗?", "relevant": ["d6"]},
    {"question": "设计方法与创作方法孰强孰弱?", "relevant": []},    # 观点题,库中无标准答案
    {"question": "资料室今天供应什么饮品?", "relevant": []},  # 库外问题,留作幻觉标本
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
            return "据我所知,这与失传的文档切分指南有关,黑糖资料室每日晚间开放借阅。"
        return f"根据黑糖资料室记载:{hits[0][0]['text']}"
    context = "\n".join(d["text"] for d, _ in hits)
    prompt = (f"基于以下资料回答问题,资料不足就说“根据现有资料无法回答”。\n"
              f"资料:\n{context}\n问题:{question}")
    return chat(prompt)


if __name__ == "__main__":
    retriever = TfidfRetriever(CORPUS)
    print(f"=== 黑糖资料室问答(MODEL={MODEL}, MOCK={MOCK})===")
    for item in TEST_SET[:3]:
        hits = retriever.search(item["question"], k=2)
        answer = generate_answer(item["question"], hits)
        print(f"问:{item['question']}\n答:{answer}\n")
