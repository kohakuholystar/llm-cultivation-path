"""t74 · s4:上线清单可执行化——YAML 配置驱动检查

上线清单如果只活在文档里,人肉核对既慢又易漏。本步把六项清单
写进 CHECKLIST_YAML,由 run_checks 逐项翻译成布尔判断,一次
运行得出通过项数,让「检查」变成可重复、可回归的流程。
"""


# === 学习契约（面向学生）===
# 本节目标：上线清单可执行化:YAML 配置驱动检查。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `load_kb(text) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按 --- 分隔符把整份素材切成知识块列表。
#   - `retrieve(query, kb, top_k=3) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按词频打分,返回最相关的 top_k 个知识块。
#   - `build_big_kb(n=200) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：构造 n 段同构知识块,模拟上规模的知识库。
#   - `bench_retrieve(kb, query, rounds=30) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：对同一查询重复检索 rounds 轮,返回每轮耗时(秒)列表。
#   - `p95(times) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：取耗时列表的 P95 分位,空列表返回 0.0。
#   - `run_checks(kb, backup_path) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：逐项执行上线清单,返回 [{name, ok, desc}] 结果列表。
#   - `run_tests(work_dir) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：把 TEST_CODE 写成 test_qa.py,再用 pytest 实跑验收。
#   - `main() -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import os
import re
import tempfile
import time
import yaml
from pathlib import Path

os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"  # 必须在 import pytest 之前
import pytest

# 用例模板:注入测试文件,由 run_tests 用 pytest 实跑
TEST_CODE = r"""import pytest
import re
import yaml


def test_load_kb_splits_chunks():
    kb = load_kb("题一\n题二\n\n---\n\n题三\n题四")
    assert kb == ["题一\n题二", "题三\n题四"]


def test_retrieve_scores_by_frequency():
    kb = ["黑糖资料室需要故障演练", "异常恢复最需要验证", "完成交付之后完成项目"]
    hits = retrieve("上线验收 完成交付", kb, top_k=3)
    assert len(hits) == 2
    assert hits[0][0] == "黑糖资料室需要故障演练"
    assert hits[0][1] == 2


def test_p95_fixed():
    assert p95([0.01, 0.02, 0.03, 0.04]) == 0.03


def test_perf_p95_within_budget():
    kb = build_big_kb(200)
    times = bench_retrieve(kb, "上线验收 故障", rounds=10)
    assert p95(times) * 1000 <= PERF_BUDGET_MS


def test_run_checks_all_pass(tmp_path):
    # TODO: 先写备份文件,断言 run_checks 返回 6 项且全部 ok
    # 提示: backup = tmp_path / "kb_backup.json";backup.write_text("{}", encoding="utf-8")
    # 提示: results = run_checks(build_big_kb(200), str(backup))
    # 提示: assert len(results) == 6 and all(r["ok"] for r in results)
    raise NotImplementedError("t74-acceptance-s4 尚未实现:请按 TODO 提示补全 test_run_checks_all_pass")


def test_run_checks_backup_missing(tmp_path):
    # TODO: 不写备份,断言备份存在项 ok 为 False
    # 提示: results = run_checks(build_big_kb(50), str(tmp_path / "nope.json"))
    # 提示: backup = next(r for r in results if r["name"] == "备份存在");assert backup["ok"] is False
    raise NotImplementedError("t74-acceptance-s4 尚未实现:请按 TODO 提示补全 test_run_checks_backup_missing")


def test_checklist_six_items():
    items = yaml.safe_load(CHECKLIST_YAML)
    assert len(items) == 6


def test_version_matches_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", APP_VERSION)
"""


TOOL_TABLE = {"calc", "echo", "quote"}

APP_VERSION = "1.2.0"

CHECKLIST_YAML = """
- {name: 知识库可加载, desc: 素材能切成块}
- {name: 检索可用, desc: 词频命中有效}
- {name: 性能达标, desc: P95 不超预算}
- {name: 工具就绪, desc: 白名单可调}
- {name: 备份存在, desc: 备份文件在}
- {name: 延迟达标, desc: 线上延迟达标}
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


def run_checks(kb, backup_path):
    """逐项执行上线清单,返回 [{name, ok, desc}] 结果列表。"""
    # TODO: 按 CHECKLIST_YAML 逐项分派六项检查,返回 [{name, ok, desc}] 结果列表
    # 提示: for item in yaml.safe_load(CHECKLIST_YAML): name = item["name"]
    # 提示: 知识库可加载 -> ok = len(kb) > 0;检索可用 -> ok = len(retrieve("验收", kb)) > 0
    # 提示: 性能达标/延迟达标 -> ok = p95(bench_retrieve(kb, "验收 故障", rounds=10)) * 1000 <= PERF_BUDGET_MS
    # 提示: 工具就绪 -> ok = "calc" in TOOL_TABLE and "echo" in TOOL_TABLE;备份存在 -> ok = Path(backup_path).exists()
    # 提示: results.append({"name": name, "ok": ok, "desc": item["desc"]});return results
    raise NotImplementedError("t74-acceptance-s4 尚未实现:请按 TODO 提示完成上线清单逐项执行")


def run_tests(work_dir):
    """把 TEST_CODE 写成 test_qa.py,再用 pytest 实跑验收。"""
    test_file = Path(work_dir) / "test_qa.py"
    names = "load_kb, retrieve, build_big_kb, bench_retrieve, p95, PERF_BUDGET_MS, APP_VERSION, CHECKLIST_YAML, run_checks"
    test_file.write_text(f"from __main__ import {names}\n" + TEST_CODE, encoding="utf-8")
    rc = pytest.main(["-q", "-o", "addopts=", "-p", "no:cacheprovider",
                      "--rootdir", str(work_dir), str(test_file)])
    assert rc == 0, f"pytest 未全过:rc={rc}"


def main():
    print("== 黑糖资料室 · 上线清单 s4 ==")
    backup = os.path.join(tempfile.gettempdir(), "kb_backup.json")
    with open(backup, "w", encoding="utf-8") as f:
        f.write('{"kb": "黑糖资料室知识库备份"}')
    results = run_checks(build_big_kb(200), backup)
    passed = sum(1 for r in results if r["ok"])
    print(f"上线清单:{len(results)} 项,通过 {passed} 项")
    with tempfile.TemporaryDirectory() as d:
        run_tests(d)


if __name__ == "__main__":
    main()
