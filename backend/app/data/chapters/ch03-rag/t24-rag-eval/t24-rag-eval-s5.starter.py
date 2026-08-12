"""黑糖资料室收官 · 第五步:忠实度评估与 Bad Case 分析——给黑糖资料室出一份体检报告。"""
# 学习契约
# 目标：完成 t24-rag-eval-s5 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 4 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：tokenize(text) -> 未标注; chat(prompt) -> 未标注; multi_search(retriever, question, k) -> 未标注; generate_answer(question, hits) -> 未标注。
# 技术栈：math, os, re, sys, collections；前置条件：在右上角 AI 配置填入自己的 DeepSeek API Key。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
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
    {"id": "d1", "text": "数据清洗方法:先统一编码与字段格式,再处理重复值和缺失值,最后写入缓存并保存质量报告。"},
    {"id": "d3", "text": "输出模板指南:先明确字段契约,再减少无效规则,并用固定样例验证输出稳定性。"},
    {"id": "d4", "text": "设计规范:版式需要统一间距、字号与颜色层级,并通过样例检查一致性。"},
    {"id": "d5", "text": "应急手册:轻微外伤先清洁并止血,必要时及时联系校医或专业人员。"},
    {"id": "d6", "text": "借阅规范:黑糖资料室的受限资料不得外传,借阅需获得管理员授权并记录用途。"},
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
    {"question": "如何学习基础指南?", "relevant": ["d1"]},
    {"question": "成员轻微外伤应该如何处理?", "relevant": ["d5"]},
    {"question": "创作方法的最高学习阶段是什么?", "relevant": ["d3"]},
    {"question": "能把受限文档带离资料室吗?", "relevant": ["d6"]},
    {"question": "设计方法与创作方法孰强孰弱?", "relevant": []},  # 观点题,库中无标准答案
    {"question": "资料室今天供应什么饮品?", "relevant": []},]  # 库外问题,幻觉标本


def chat(prompt):  # 调 DeepSeek;异常返回带标记文本,评估流程不中断
    try:
        resp = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0)
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        return f"[LLM 调用失败] {exc}"


MOCK_REWRITES = {  # 离线演示的固定改写表;"创作方法"一题改写故意不给力,留作 bad case;Q1 单查已命中,无需改写
    "成员轻微外伤应该如何处理?": ["轻微外伤如何止血", "止血处理如何配制", "外伤出血后如何寻求帮助"],
    "创作方法的最高学习阶段是什么?": ["方案术的真谛是什么", "如何做到优先识别相关信号", "设计原理的核心思想"],
    "能把受限文档带离资料室吗?": ["资料借阅有什么规矩", "受限文档能否对外分享", "借阅授权如何申请"],
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
        return (f"根据黑糖资料室记载:{hits[0][0]['text']}" if hits else
                "据我所知,这与失传的文档切分指南有关,黑糖资料室每日晚间开放借阅。")
    context = "\n".join(d["text"] for d, _ in hits)
    return chat(f"基于以下资料回答,资料不足就说“根据现有资料无法回答”。\n资料:\n{context}\n问题:{question}")


def check_faithfulness(answer, hits):
    """忠实度:答案须被检索资料支撑。MOCK 用前缀启发式;真实环境让 LLM 当裁判。"""
    # TODO: MOCK 用前缀启发式,真实分支让 LLM 当裁判,返回是否忠实
    # 提示: MOCK 分支 return answer.startswith("根据黑糖资料室记载:");真实分支把资料与答案拼进裁判 prompt,return "忠实" in chat(prompt)
    raise NotImplementedError("t24-s5 尚未实现:请按 TODO 提示完成 check_faithfulness 忠实度判定")


def diagnose(relevant, hit_ids, faithful):  # 失败分类学(按优先级归类):不同问题,不同方案
    # TODO: 按优先级给失败分类:检索失败 → 误检 → 生成幻觉 → 通过/正确拒绝,返回 (诊断, 改进建议)
    # 提示: relevant 非空且 set(hit_ids) & set(relevant) 为空 → ("检索失败", 改进建议);relevant 空但 hit_ids 非空 → ("误检", 改进建议);not faithful → ("生成幻觉", 改进建议);否则 ("通过", "") if relevant else ("正确拒绝", "")
    raise NotImplementedError("t24-s5 尚未实现:请按 TODO 提示完成 diagnose 失败分类")


if __name__ == "__main__":
    retriever = TfidfRetriever(CORPUS)
    print(f"=== 黑糖资料室质量体检报告(MOCK={MOCK})===")
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
        print(f"  {verdict} | {question} | 建议:{fix}")
