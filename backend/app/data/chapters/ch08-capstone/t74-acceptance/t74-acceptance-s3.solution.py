"""t74 · s3:性能基线——P95 百分位与预算判定

功能正确不等于可以上线。本步为检索建立性能基线:构造大规模
知识库,反复计时取统计量,用 P95 与预算比较,输出达标结论。
"""
import os
import tempfile
import time
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


@pytest.mark.parametrize("a,b,op,expect", [(3, 4, "add", 7), (3, 4, "mul", 12), (2, 5, "pow", 32)])
def test_calc_ops(a, b, op, expect):
    assert dispatch_tool("calc", (a, b, op)) == expect


def test_unknown_tool():
    msg = dispatch_tool("fly", ())
    assert "未知工具" in msg and "calc" in msg


def test_big_kb_size():
    assert len(build_big_kb(200)) == 200


def test_bench_length():
    kb = build_big_kb(50)
    times = bench_retrieve(kb, "上线验收 故障", rounds=10)
    assert len(times) == 10


def test_p95_fixed():
    assert p95([0.01, 0.02, 0.03, 0.04]) == 0.03


def test_perf_p95_within_budget():
    kb = build_big_kb(200)
    times = bench_retrieve(kb, "上线验收 故障", rounds=10)
    assert p95(times) * 1000 <= PERF_BUDGET_MS
"""


TOOL_TABLE = {"calc", "echo", "quote"}

_CALC = {
    "add": lambda a, b: a + b,
    "mul": lambda a, b: a * b,
    "pow": lambda a, b: a ** b,
}


def dispatch_tool(name, args):
    """白名单分派:只认 TOOL_TABLE 里的工具,calc 内部再查 _CALC。"""
    if name not in TOOL_TABLE:
        return f"未知工具 {name},可用的工具: {', '.join(sorted(TOOL_TABLE))}"
    if name == "calc":
        a, b, op = args
        if op not in _CALC:
            return f"未知运算 {op}"
        return _CALC[op](a, b)
    if name == "echo":
        return args
    return f"「{args}」"


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


def build_big_kb(n=200):
    """构造 n 段同构知识块,模拟上规模的知识库。"""
    return [f"第{i}段:上线验收之道,先验证故障恢复,再检查完成交付所需工具。" for i in range(1, n + 1)]


def bench_retrieve(kb, query, rounds=30):
    """对同一查询重复检索 rounds 轮,返回每轮耗时(秒)列表。"""
    times = []
    for _ in range(rounds):
        t0 = time.perf_counter()
        retrieve(query, kb)
        times.append(time.perf_counter() - t0)
    return times


def p95(times):
    """取耗时列表的 P95 分位,空列表返回 0.0。"""
    if not times:
        return 0.0
    o = sorted(times)
    return o[int(len(o) * 0.95) - 1]


PERF_BUDGET_MS = 50.0


def run_perf(kb):
    """打印性能基线与预算达标结论。"""
    times = bench_retrieve(kb, "上线验收 故障")
    values = [t * 1000 for t in times]
    ok = p95(values) <= PERF_BUDGET_MS
    print(f"性能基线(ms):min={min(values):.2f} p50={sorted(values)[len(values) // 2]:.2f} "
          f"p95={p95(values):.2f} max={max(values):.2f}")
    print(f"达标={'是' if ok else '否'}(预算 {PERF_BUDGET_MS} ms)")


def run_tests(work_dir):
    """把 TEST_CODE 写成 test_qa.py,再用 pytest 实跑验收。"""
    test_file = Path(work_dir) / "test_qa.py"
    names = "load_kb, retrieve, dispatch_tool, build_big_kb, bench_retrieve, p95, PERF_BUDGET_MS"
    test_file.write_text(f"from __main__ import {names}\n" + TEST_CODE, encoding="utf-8")
    rc = pytest.main(["-q", "-o", "addopts=", "-p", "no:cacheprovider",
                      "--rootdir", str(work_dir), str(test_file)])
    assert rc == 0, f"pytest 未全过:rc={rc}"


def main():
    print("== 黑糖资料室 · 性能基线 s3 ==")
    kb = build_big_kb(200)
    run_perf(kb)
    with tempfile.TemporaryDirectory() as d:
        run_tests(d)
    print("pytest 全部通过:10 个用例")


if __name__ == "__main__":
    main()
