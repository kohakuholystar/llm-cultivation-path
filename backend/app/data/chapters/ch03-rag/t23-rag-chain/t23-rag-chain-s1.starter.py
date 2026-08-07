"""藏经阁第 1 步:秘籍语料库与文档切块。

RAG 的一切从语料开始:先把每部秘籍登记成带出处元数据的文档,
再切成适合检索的小块(chunk),为后续向量化做准备。
"""

CHUNK_SIZE = 60     # 每个切片的最大字符数
CHUNK_OVERLAP = 15  # 相邻切片重叠的字符数,防止语义被拦腰切断

# 藏经阁秘籍总目:每部秘籍都有唯一编号、出处和正文
DOCUMENTS = [
    {
        "doc_id": "yjj",
        "source": "《易筋经·卷一》",
        "content": "易筋经乃少林镇寺之宝,讲究以意导气、以气运力。修习者需每日寅时起身,面东而立,先行吐纳三十六次,再依图谱摆出十二式桩架。初学者切忌贪快,桩架不正则气行偏差,轻则筋骨酸痛,重则伤及经络。经中明言:宁可十日不进阶,不可一日错行功。",
    },
    {
        "doc_id": "jy",
        "source": "《九阳真经·总纲》",
        "content": "九阳真经重在内力生生不息。其总纲云:他强由他强,清风拂山岗。修习九阳神功者,内力自行周天运转,寒暑不侵,百毒难伤。然此功进境极缓,非有大毅力者不能成。觉远大师于华山之巅口述此经,张君宝与郭襄各得一部分,后衍化为武当、峨眉两派内功根基。",
    },
    {
        "doc_id": "dg",
        "source": "《独孤九剑·剑理篇》",
        "content": "独孤九剑共九式,破尽天下武功。其核心剑理只有四个字:料敌机先。风清扬传令狐冲时言:剑招是死的,人是活的,无招胜有招。破剑式用以破解各派剑法,破刀式克制单刀双刀,破气式则专克内功深厚的对手。习此剑者须忘却固定招式,只记剑意。",
    },
    {
        "doc_id": "qk",
        "source": "《乾坤大挪移·心法》",
        "content": "乾坤大挪移为明教镇教神功,共分七层。其要义在于激发人体潜力、挪移乾坤二气。第一层需七年苦修,第二层加倍,层层递进。张无忌因身具九阳神功,内力深厚,方能在密道中速成。此功最忌根基不牢而强行冲关,历代教主多有因此殒命者。",
    },
]


def chunk_documents(documents, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """把每部秘籍切成定长小块,每块都携带出处元数据。"""
    chunks, step = [], max(chunk_size - overlap, 1)  # 滑动窗口的实际步长
    for doc in documents:
        text = doc["content"]
        # TODO: 用滑动窗口把正文切成定长小块,每块携带出处与编号
        # 提示: for start in range(0, len(text), step): piece = text[start:start + chunk_size]; 向 chunks 追加 {"text": piece, "source": doc["source"], "doc_id": doc["doc_id"]}
        raise NotImplementedError("t23-s1 尚未实现:请按 TODO 提示完成切块逻辑")
    return chunks


def preview_chunks(chunks, count=3):
    """打印前几个切片,检查切块是否正确保留了出处。"""
    print(f"共切分出 {len(chunks)} 个片段\n")
    for i, chunk in enumerate(chunks[:count], start=1):
        print(f"--- 片段 {i} | 出处:{chunk['source']} ---")
        print(chunk["text"])


def main():
    chunks = chunk_documents(DOCUMENTS)
    preview_chunks(chunks)


if __name__ == "__main__":
    main()
