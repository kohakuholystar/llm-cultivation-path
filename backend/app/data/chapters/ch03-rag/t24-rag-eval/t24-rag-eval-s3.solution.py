"""黑糖资料室收官 · 第三步:召回率评估——给检索器一把量化的尺子。

用第二步之前的纯检索代码(不带 LLM),对标注测试集逐题打分:
能答的题算 Recall@k,库外的题算"正确拒绝",两类指标分开统计。
"""
import math
import re
from collections import Counter

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


def effective_hits(hits):
    """过滤零分结果:得分 0 只是"最不坏"的凑数,不是命中,留着会让召回率虚高。"""
    return [doc for doc, score in hits if score > 0]


def recall_at_k(retrieved_ids, relevant):
    """Recall@k = 命中的相关文档数 / 相关文档总数;库外题返回 None(无定义,不是 0)。"""
    if not relevant:
        return None
    return sum(1 for i in retrieved_ids if i in relevant) / len(relevant)


def evaluate_retriever(retriever, test_set, k=2):
    """逐题跑检索并打分,返回 (rows, summary) 两类指标分开统计。"""
    rows, recalls, reject_ok, reject_total = [], [], 0, 0
    for item in test_set:
        hits = effective_hits(retriever.search(item["question"], k=k))
        ids = [d["id"] for d in hits]
        recall = recall_at_k(ids, item["relevant"])
        if recall is None:                      # 库外问题:正确行为是一篇都别检出来
            reject_total += 1
            reject_ok += not ids                # 空命中 = 正确拒绝
            rows.append((item["question"], ids, "正确拒绝" if not ids else "误检"))
        else:
            recalls.append(recall)
            rows.append((item["question"], ids, f"Recall={recall:.2f}"))
    summary = {
        "avg_recall": sum(recalls) / len(recalls) if recalls else 0.0,
        "reject_rate": reject_ok / reject_total if reject_total else 1.0,
    }
    return rows, summary


if __name__ == "__main__":
    retriever = TfidfRetriever(CORPUS)
    print("=== 黑糖资料室检索评估报告(Recall@2)===")
    rows, summary = evaluate_retriever(retriever, TEST_SET, k=2)
    for question, ids, verdict in rows:
        print(f"{question} | 命中 {ids} | {verdict}")
    print(f"\n平均 Recall@2: {summary['avg_recall']:.2f}")
    print(f"库外问题拒绝率: {summary['reject_rate']:.0%}")
