"""黑糖资料室收官 · 第二步:接入 DeepSeek 生成端(检索 → 拼 prompt → 回答)。"""
# 学习契约
# 目标：完成 t24-rag-eval-s2 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 4 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：tokenize(text) -> 未标注; chat(prompt) -> 未标注; generate_answer(question, hits) -> 未标注。
# 技术栈：math, os, re, sys, collections；前置条件：在右上角 AI 配置填入自己的 DeepSeek API Key。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
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
    # TODO: 调 DeepSeek 对话接口并返回文本,异常时返回带标记的错误说明
    # 提示: resp = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0);return resp.choices[0].message.content.strip();except Exception as exc: return f"[LLM 调用失败] {exc}"
    raise NotImplementedError("t24-s2 尚未实现:请按 TODO 提示完成 chat 调用")


def generate_answer(question, hits):
    """检索+生成:把 top 文档拼进 prompt,要求资料不足时如实拒答。"""
    # TODO: MOCK 与真实两分支:检索失败时故意瞎答制造幻觉标本,命中时引用原文,真实分支拼 prompt 调 LLM
    # 提示: MOCK 下 not hits 或 hits[0][1] == 0 时返回固定瞎答句,否则返回 f"根据黑糖资料室记载:{hits[0][0]['text']}";真实分支 context = "\n".join(d["text"] for d, _ in hits),拼"资料不足就说无法回答"的 prompt,return chat(prompt)
    raise NotImplementedError("t24-s2 尚未实现:请按 TODO 提示完成 generate_answer 拼资料生成")


if __name__ == "__main__":
    retriever = TfidfRetriever(CORPUS)
    print(f"=== 黑糖资料室问答(MODEL={MODEL}, MOCK={MOCK})===")
    for item in TEST_SET[:3]:
        hits = retriever.search(item["question"], k=2)
        answer = generate_answer(item["question"], hits)
        print(f"问:{item['question']}\n答:{answer}\n")
