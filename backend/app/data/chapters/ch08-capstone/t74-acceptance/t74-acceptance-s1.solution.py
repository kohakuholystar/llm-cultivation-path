"""t74 · s1:集成测试初阵——pytest 真跑真验证

项目「终期交付」上线前要过三道关:功能、性能、部署。本步搭起
集成测试的台子:把知识库问答拆成可测的纯函数,再用 pytest
按真实 CLI 流程逐用例验收。
"""
import os
import tempfile
from pathlib import Path

os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"  # 必须在 import pytest 之前
import pytest

# 用例模板:注入测试文件,由 run_tests 用 pytest 实跑
TEST_CODE = r"""import pytest


def test_load_kb_splits_chunks():
    kb = load_kb("题一\n题二\n\n---\n\n题三\n题四")
    assert kb == ["题一\n题二", "题三\n题四"]


def test_retrieve_scores_by_frequency():
    kb = ["黑糖资料室需要故障演练", "异常恢复最需要验证", "完成交付之后完成项目"]
    hits = retrieve("上线验收 完成交付", kb, top_k=3)
    assert len(hits) == 2
    assert hits[0][0] == "黑糖资料室需要故障演练"
    assert hits[0][1] == 2


def test_format_answer_joins_hits():
    hits = [("黑糖资料室需要故障演练", 2, 0), ("完成交付之后完成项目", 1, 2)]
    assert format_answer(hits) == "[1] 黑糖资料室需要故障演练(来源片段 0)\n[2] 完成交付之后完成项目(来源片段 2)"


def test_pipeline_end_to_end():
    kb = load_kb("上线验收需故障\n\n---\n\n完成交付需工具")
    ans = format_answer(retrieve("故障", kb))
    assert "[1] 上线验收需故障" in ans
"""


def load_kb(text):
    """按 --- 分隔符把整份素材切成知识块列表。"""
    return [c.strip() for c in text.split("---")]


def retrieve(query, kb, top_k=3):
    """按词频打分,返回最相关的 top_k 个知识块。"""
    q_words = query.split()
    scored = [(c, sum(c.count(w) for w in q_words), i) for i, c in enumerate(kb)]
    hits = sorted((t for t in scored if t[1] > 0), key=lambda t: t[1], reverse=True)
    return hits[:top_k]


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
