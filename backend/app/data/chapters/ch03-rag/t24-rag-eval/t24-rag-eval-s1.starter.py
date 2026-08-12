"""黑糖资料室收官 · 第一步:搭建检索基线与标注测试集。

评估先行:先固定语料、检索器和标尺(测试集),之后的每次优化才有据可依。
"""
# 学习契约
# 目标：完成 t24-rag-eval-s1 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 4 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：tokenize(text) -> 未标注。
# 技术栈：math, re, collections。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
import math
import re
from collections import Counter

# ---------- 黑糖资料室迷你语料(真实系统中对应 chunk 后的文档库) ----------
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
    """纯 Python TF-IDF 检索器:离线、确定性,评估实验可精确复现。"""

    def __init__(self, docs):
        self.docs = docs
        self.tf = [Counter(tokenize(d["text"])) for d in docs]  # 每条文档的词频表
        df = Counter()
        for counts in self.tf:  # 文档频率:该词出现在多少条文档中
            for term in counts:
                df[term] += 1
        n = len(docs)
        # 平滑 idf:出现越普遍的词权重越低,+1 防止除零与负值
        self.idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}

    def search(self, query, k=3):
        """对每条文档按查询词 tf·idf 求和打分,降序返回 [(doc, score)] 前 k 条。"""
        # TODO: 对每条文档按查询词 tf·idf 求和打分,降序返回前 k 条
        # 提示: score = sum(counts.get(t, 0) * self.idf.get(t, 0.0) for t in tokenize(query));scored.sort(key=lambda x: x[1], reverse=True);return scored[:k]
        raise NotImplementedError("t24-s1 尚未实现:请按 TODO 提示完成 search 打分排序")


# ---------- 标注测试集:relevant 是人工标注的相关文档 id(评估的标尺) ----------
TEST_SET = [
    {"question": "如何学习基础指南?", "relevant": ["d1"]},
    {"question": "成员轻微外伤应该如何处理?", "relevant": ["d5"]},
    {"question": "创作方法的最高学习阶段是什么?", "relevant": ["d3"]},
    {"question": "能把受限文档带离资料室吗?", "relevant": ["d6"]},
    {"question": "设计方法与创作方法孰强孰弱?", "relevant": []},    # 观点题,库中无标准答案
    {"question": "资料室今天供应什么饮品?", "relevant": []},  # 库外问题,留作幻觉标本
]

if __name__ == "__main__":
    retriever = TfidfRetriever(CORPUS)
    print("=== 黑糖资料室检索基线 · 冒烟测试 ===")
    # TODO: 遍历测试集前 3 题,打印每题 top-2 命中与标注
    # 提示: for item in TEST_SET[:3]:hits = retriever.search(item["question"], k=2);top = ", ".join(f"{d['id']}({s:.2f})" for d, s in hits);print(f"问:{item['question']}\n  top-2 → {top}  标注 → {item['relevant']}")
    raise NotImplementedError("t24-s1 尚未实现:请按 TODO 提示完成冒烟测试")
