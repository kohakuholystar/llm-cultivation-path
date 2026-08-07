"""藏经阁收官 · 第一步:搭建检索基线与标注测试集。

评估先行:先固定语料、检索器和标尺(测试集),之后的每次优化才有据可依。
"""
import math
import re
from collections import Counter

# ---------- 藏经阁迷你语料(真实系统中对应 chunk 后的文档库) ----------
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
    {"question": "如何修炼内功?", "relevant": ["d1"]},
    {"question": "弟子受伤流血该用什么药?", "relevant": ["d5"]},
    {"question": "剑法的最高境界是什么?", "relevant": ["d3"]},
    {"question": "能把经书带回厢房研读吗?", "relevant": ["d6"]},
    {"question": "拳法与剑法孰强孰弱?", "relevant": []},    # 观点题,库中无标准答案
    {"question": "禅师的床底下藏着什么?", "relevant": []},  # 库外问题,留作幻觉标本
]

if __name__ == "__main__":
    retriever = TfidfRetriever(CORPUS)
    print("=== 藏经阁检索基线 · 冒烟测试 ===")
    # TODO: 遍历测试集前 3 题,打印每题 top-2 命中与标注
    # 提示: for item in TEST_SET[:3]:hits = retriever.search(item["question"], k=2);top = ", ".join(f"{d['id']}({s:.2f})" for d, s in hits);print(f"问:{item['question']}\n  top-2 → {top}  标注 → {item['relevant']}")
    raise NotImplementedError("t24-s1 尚未实现:请按 TODO 提示完成冒烟测试")
