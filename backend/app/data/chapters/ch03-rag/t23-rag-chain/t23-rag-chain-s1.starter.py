"""黑糖资料室第 1 步:参考资料语料库与文档切块。

RAG 的一切从语料开始:先把每部参考资料登记成带出处元数据的文档,
再切成适合检索的小块(chunk),为后续向量化做准备。
"""
# 学习契约
# 目标：完成 t23-rag-chain-s1 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 2 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：chunk_documents(documents, chunk_size, overlap) -> 未标注; preview_chunks(chunks, count) -> 未标注; main() -> 未标注。
# 技术栈：Python 标准库。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。

CHUNK_SIZE = 60     # 每个切片的最大字符数
CHUNK_OVERLAP = 15  # 相邻切片重叠的字符数,防止语义被拦腰切断

# 黑糖资料室参考资料总目:每部参考资料都有唯一编号、出处和正文
DOCUMENTS = [
    {
        "doc_id": "yjj",
        "source": "《文档切分指南·第一章》",
        "content": "文档切分指南是资料组的核心文档。处理前先统一编码与换行,再按标题、段落和长度边界切分。初学者不要只追求切块数量:片段过短会丢失上下文,片段过长会降低检索精度。每次调整参数后都应保存样例并复查引用是否仍能回到原文。",
    },
    {
        "doc_id": "jy",
        "source": "《检索基础指南·总纲》",
        "content": "检索基础指南强调召回稳定性。查询进入系统后先规范化文本,再从索引中取得候选片段。候选不足时应记录未命中的查询,而不是让生成模型补写事实。资料组、开发组和测试组分别维护数据、实现与回归样例。",
    },
    {
        "doc_id": "dg",
        "source": "《重排设计指南》",
        "content": "重排设计指南介绍如何把更相关的候选放到前面。先保留召回阶段的候选集,再结合关键词覆盖、来源质量和位置特征计算分数。同分结果使用稳定的文档编号排序,避免多次运行顺序漂移。",
    },
    {
        "doc_id": "qk",
        "source": "《黑糖资料室·检索设计》",
        "content": "黑糖资料室采用分层检索设计,共分数据加载、文本切分、候选召回、结果重排与引用生成五层。其要义是让回答始终能回到原始资料。第一层负责统一格式,第二层保留上下文边界,后续层逐步提高相关性。若跳过数据质量检查直接生成回答,结果容易失去可靠来源。",
    },
]


def chunk_documents(documents, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """把每部参考资料切成定长小块,每块都携带出处元数据。"""
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
