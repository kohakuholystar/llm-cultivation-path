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
    kb = ["渡劫飞升需要雷劫淬体", "心魔劫最难渡过", "飞升之后成仙"]
    hits = retrieve("渡劫 飞升", kb, top_k=3)
    assert len(hits) == 2
    assert hits[0][0] == "渡劫飞升需要雷劫淬体"
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
    # TODO: 断言 bench_retrieve 返回的耗时列表长度等于 rounds
    # 提示: kb = build_big_kb(50)
    # 提示: times = bench_retrieve(kb, "渡劫 雷劫", rounds=10);assert len(times) == 10
    raise NotImplementedError("t74-acceptance-s3 尚未实现:请按 TODO 提示补全 test_bench_length")


def test_p95_fixed():
    # TODO: 断言 p95 取排序后第 95 百分位
    # 提示: assert p95([0.01, 0.02, 0.03, 0.04]) == 0.03
    raise NotImplementedError("t74-acceptance-s3 尚未实现:请按 TODO 提示补全 test_p95_fixed")


def test_perf_p95_within_budget():
    # TODO: 两百段知识库计时后,断言 p95 换算毫秒不超 PERF_BUDGET_MS
    # 提示: kb = build_big_kb(200)
    # 提示: times = bench_retrieve(kb, "渡劫 雷劫", rounds=10)
    # 提示: assert p95(times) * 1000 <= PERF_BUDGET_MS
    raise NotImplementedError("t74-acceptance-s3 尚未实现:请按 TODO 提示补全 test_perf_p95_within_budget")
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
    return [f"第{i}段:渡劫之道,雷劫在前心劫在后,飞升者需护体法器。" for i in range(1, n + 1)]


def bench_retrieve(kb, query, rounds=30):
    """对同一查询重复检索 rounds 轮,返回每轮耗时(秒)列表。"""
    # TODO: 用 perf_counter 前后计时,循环 rounds 轮收集每轮耗时(秒)
    # 提示: times = []
    # 提示: for _ in range(rounds):
    # 提示:     t0 = time.perf_counter();retrieve(query, kb);times.append(time.perf_counter() - t0)
    # 提示: return times
    raise NotImplementedError("t74-acceptance-s3 尚未实现:请按 TODO 提示实现反复计时取耗时")


def p95(times):
    """取耗时列表的 P95 分位,空列表返回 0.0。"""
    # TODO: 排序后取第 95 百分位,空列表返回 0.0
    # 提示: if not times: return 0.0
    # 提示: o = sorted(times);return o[int(len(o) * 0.95) - 1]
    raise NotImplementedError("t74-acceptance-s3 尚未实现:请按 TODO 提示实现 P95 分位计算")


PERF_BUDGET_MS = 50.0


def run_perf(kb):
    """打印性能基线与预算达标结论。"""
    # TODO: 耗时转毫秒,打印 min/p50/p95/max 与预算达标结论
    # 提示: times = bench_retrieve(kb, "渡劫 雷劫");values = [t * 1000 for t in times]
    # 提示: ok = p95(values) <= PERF_BUDGET_MS
    # 提示: print(f"性能基线(ms):min={min(values):.2f} p50={sorted(values)[len(values) // 2]:.2f} p95={p95(values):.2f} max={max(values):.2f}")
    # 提示: print(f"达标={'是' if ok else '否'}(预算 {PERF_BUDGET_MS} ms)")
    raise NotImplementedError("t74-acceptance-s3 尚未实现:请按 TODO 提示实现性能基线打印")


def run_tests(work_dir):
    """把 TEST_CODE 写成 test_qa.py,再用 pytest 实跑验收。"""
    test_file = Path(work_dir) / "test_qa.py"
    names = "load_kb, retrieve, dispatch_tool, build_big_kb, bench_retrieve, p95, PERF_BUDGET_MS"
    test_file.write_text(f"from __main__ import {names}\n" + TEST_CODE, encoding="utf-8")
    rc = pytest.main(["-q", "-o", "addopts=", "-p", "no:cacheprovider",
                      "--rootdir", str(work_dir), str(test_file)])
    assert rc == 0, f"pytest 未全过:rc={rc}"


def main():
    print("== 渡劫飞升 · 性能基线 s3 ==")
    kb = build_big_kb(200)
    run_perf(kb)
    with tempfile.TemporaryDirectory() as d:
        run_tests(d)
    print("pytest 全部通过:10 个用例")


if __name__ == "__main__":
    main()
