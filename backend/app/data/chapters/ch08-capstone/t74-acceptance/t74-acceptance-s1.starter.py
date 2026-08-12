"""t74 · s1:集成测试初阵——pytest 真跑真验证

项目「终期交付」上线前要过三道关:功能、性能、部署。本步搭起
集成测试的台子:把知识库问答拆成可测的纯函数,再用 pytest
按真实 CLI 流程逐用例验收。
"""


# === 学习契约（面向学生）===
# 本节目标：集成测试初阵:pytest 真跑真验证。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `load_kb(text) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按 --- 分隔符把整份素材切成知识块列表。
#   - `retrieve(query, kb, top_k=3) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按词频打分,返回最相关的 top_k 个知识块。
#   - `format_answer(hits) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：把命中结果排版成可直接回复的答案文本。
#   - `run_tests(work_dir) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：把 TEST_CODE 写成 test_qa.py,再用 pytest 实跑验收。
#   - `main() -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import os
import tempfile
from pathlib import Path

os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"  # 必须在 import pytest 之前
import pytest

# 用例模板:注入测试文件,由 run_tests 用 pytest 实跑
TEST_CODE = r"""import pytest


def test_load_kb_splits_chunks():
    # TODO: 构造含 --- 分隔符的素材,断言 load_kb 切分出的知识块列表
    # 提示: kb = load_kb("题一\n题二\n\n---\n\n题三\n题四")
    # 提示: assert kb == ["题一\n题二", "题三\n题四"]
    raise NotImplementedError("t74-acceptance-s1 尚未实现:请按 TODO 提示补全 test_load_kb_splits_chunks")


def test_retrieve_scores_by_frequency():
    # TODO: 断言 retrieve 按词频得分排序并截断到 top_k
    # 提示: kb = ["黑糖资料室需要故障演练", "异常恢复最需要验证", "完成交付之后完成项目"]
    # 提示: hits = retrieve("上线验收 完成交付", kb, top_k=3)
    # 提示: assert len(hits) == 2;assert hits[0][0] == "黑糖资料室需要故障演练";assert hits[0][1] == 2
    raise NotImplementedError("t74-acceptance-s1 尚未实现:请按 TODO 提示补全 test_retrieve_scores_by_frequency")


def test_format_answer_joins_hits():
    # TODO: 断言 format_answer 把命中三元组排版成「序号 内容(来源片段 编号)」
    # 提示: hits = [("黑糖资料室需要故障演练", 2, 0), ("完成交付之后完成项目", 1, 2)]
    # 提示: assert format_answer(hits) == "[1] 黑糖资料室需要故障演练(来源片段 0)\n[2] 完成交付之后完成项目(来源片段 2)"
    raise NotImplementedError("t74-acceptance-s1 尚未实现:请按 TODO 提示补全 test_format_answer_joins_hits")


def test_pipeline_end_to_end():
    # TODO: 串联 load_kb 到 retrieve 再到 format_answer,断言答案包含目标知识块
    # 提示: kb = load_kb("上线验收需故障\n\n---\n\n完成交付需工具")
    # 提示: ans = format_answer(retrieve("故障", kb));assert "[1] 上线验收需故障" in ans
    raise NotImplementedError("t74-acceptance-s1 尚未实现:请按 TODO 提示补全 test_pipeline_end_to_end")
"""


def load_kb(text):
    """按 --- 分隔符把整份素材切成知识块列表。"""
    return [c.strip() for c in text.split("---")]


def retrieve(query, kb, top_k=3):
    """按词频打分,返回最相关的 top_k 个知识块。"""
    # TODO: 按词频给知识块打分并降序截取 top_k
    # 提示: q_words = query.split()
    # 提示: scored = [(c, sum(c.count(w) for w in q_words), i) for i, c in enumerate(kb)]
    # 提示: hits = sorted((t for t in scored if t[1] > 0), key=lambda t: t[1], reverse=True)
    # 提示: return hits[:top_k]
    raise NotImplementedError("t74-acceptance-s1 尚未实现:请按 TODO 提示实现按词频打分检索")


def format_answer(hits):
    """把命中结果排版成可直接回复的答案文本。"""
    if not hits:
        return "未检索到相关资料"
    return "\n".join(f"[{i}] {c}(来源片段 {n})" for i, (c, s, n) in enumerate(hits, 1))


def run_tests(work_dir):
    """把 TEST_CODE 写成 test_qa.py,再用 pytest 实跑验收。"""
    test_file = Path(work_dir) / "test_qa.py"
    code = "from __main__ import load_kb, retrieve, format_answer\n" + TEST_CODE
    test_file.write_text(code, encoding="utf-8")
    rc = pytest.main(["-q", "-o", "addopts=", "-p", "no:cacheprovider",
                      "--rootdir", str(work_dir), str(test_file)])
    assert rc == 0, f"pytest 未全过:rc={rc}"


def main():
    print("== 黑糖资料室 · 集成测试 s1 ==")
    kb = load_kb("上线验收需要覆盖故障\n\n---\n\n异常情况故障最难\n\n---\n\n完成交付需工具")
    print(format_answer(retrieve("上线验收", kb)))
    with tempfile.TemporaryDirectory() as d:
        run_tests(d)
    print("pytest 全部通过:4 个用例")


if __name__ == "__main__":
    main()
