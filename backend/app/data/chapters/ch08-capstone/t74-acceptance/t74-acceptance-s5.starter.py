"""t74 · s5:项目复盘与上线确认——报告聚合 + 一键上线

四段式复盘报告把测试、性能、清单聚合成结论,全过才可上线。"""


# === 学习契约（面向学生）===
# 本节目标：项目复盘与上线确认:报告聚合 + 上线门禁。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `load_kb(text) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `retrieve(query, kb, top_k=3) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `bench_retrieve(kb, query, rounds=30) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `p95(times) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `run_checks(kb, backup_path) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `build_report(stats, perf_ms, checks) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `run_tests(work_dir) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `main() -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import os
import tempfile
import time
import yaml
from pathlib import Path

os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"  # 必须在 import pytest 之前
import pytest

# 用例模板:注入测试文件,由 run_tests 用 pytest 实跑
TEST_CODE = r"""import pytest


def test_load_kb_splits_chunks():
    kb = load_kb("题一\n题二\n\n---\n\n题三\n题四")
    assert kb == ["题一\n题二", "题三\n题四"]


def test_retrieve_scores_by_frequency():
    hits = retrieve("上线验收 完成交付", ["黑糖资料室需要故障演练", "异常恢复最需要验证", "完成交付之后完成项目"])
    assert hits[0][0] == "黑糖资料室需要故障演练"


def test_p95_fixed():
    assert p95([0.01, 0.02, 0.03, 0.04]) == 0.03


def test_perf_p95_within_budget():
    assert p95(bench_retrieve(KB, "上线验收 故障", rounds=10)) * 1000 <= PERF_BUDGET_MS


def test_run_checks_all_pass(tmp_path):
    (tmp_path / "kb_backup.json").write_text("{}", encoding="utf-8")
    results = run_checks(KB, str(tmp_path / "kb_backup.json"))
    assert len(results) == 6 and all(r["ok"] for r in results)


def test_run_checks_backup_missing(tmp_path):
    r = next(x for x in run_checks(KB, str(tmp_path / "nope.json")) if x["name"] == "备份存在")
    assert r["ok"] is False


def test_report_sections():
    # TODO: 断言 build_report 生成的报告包含四个固定节次标题
    # 提示: r = build_report((TEST_TOTAL, TEST_TOTAL, 0), 1.0, [])
    # 提示: assert "## 1 测试统计" in r and "## 4 结论" in r
    raise NotImplementedError("t74-acceptance-s5 尚未实现:请按 TODO 提示补全 test_report_sections")


def test_report_ok():
    # TODO: 全部通过时,断言结论为「可以上线上线验收!」
    # 提示: r = build_report((TEST_TOTAL, TEST_TOTAL, 0), 1.0, [{"name": "a", "ok": True, "desc": "d"}] * 6)
    # 提示: assert "可以上线上线验收!" in r
    raise NotImplementedError("t74-acceptance-s5 尚未实现:请按 TODO 提示补全 test_report_ok")


def test_report_blocked():
    # TODO: 存在失败时,断言结论为「禁止上线」
    # 提示: r = build_report((TEST_TOTAL, 0, TEST_TOTAL), 1.0, [{"name": "a", "ok": False, "desc": "d"}])
    # 提示: assert "禁止上线" in r
    raise NotImplementedError("t74-acceptance-s5 尚未实现:请按 TODO 提示补全 test_report_blocked")
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

KB = ["上线验收需要覆盖故障", "异常恢复最需要验证", "完成交付需工具"]

TEST_TOTAL = 9

PERF_BUDGET_MS = 50.0


def load_kb(text):
    return [c.strip() for c in text.split("---")]


def retrieve(query, kb, top_k=3):
    q_words = query.split()
    scored = [(c, sum(c.count(w) for w in q_words), i) for i, c in enumerate(kb)]
    hits = sorted((t for t in scored if t[1] > 0), key=lambda t: t[1], reverse=True)
    return hits[:top_k]


def bench_retrieve(kb, query, rounds=30):
    times = []
    for _ in range(rounds):
        t0 = time.perf_counter()
        retrieve(query, kb)
        times.append(time.perf_counter() - t0)
    return times


def p95(times):
    if not times:
        return 0.0
    o = sorted(times)
    return o[int(len(o) * 0.95) - 1]


def run_checks(kb, backup_path):
    lat = lambda: p95(bench_retrieve(kb, "上线验收 故障", rounds=10)) * 1000 <= PERF_BUDGET_MS
    checks = {
        "知识库可加载": lambda: len(kb) > 0,
        "检索可用": lambda: len(retrieve("上线验收", kb)) > 0,
        "性能达标": lat,
        "工具就绪": lambda: "calc" in TOOL_TABLE,
        "备份存在": lambda: Path(backup_path).exists(),
        "延迟达标": lat,
    }
    return [{"name": i["name"], "ok": checks[i["name"]](), "desc": i["desc"]}
            for i in yaml.safe_load(CHECKLIST_YAML)]


def build_report(stats, perf_ms, checks):
    # TODO: 生成四段式复盘报告,并用与运算聚合三关结论
    # 提示: total, passed, failed = stats
    # 提示: ok = failed == 0 and perf_ms <= PERF_BUDGET_MS and all(c["ok"] for c in checks)
    # 提示: lines = ["# 终期交付 · 上线复盘报告", "", "## 1 测试统计",
    # 提示:         f"共 {total} 个用例,通过 {passed} 个,失败 {failed} 个", "",
    # 提示:         "## 2 性能基线", f"检索 P95 = {perf_ms:.1f} ms(预算 {PERF_BUDGET_MS} ms)", "",
    # 提示:         "## 3 上线清单", ""]
    # 提示: lines += [f"- {c['name']}:{'通过' if c['ok'] else '未通过'}" for c in checks]
    # 提示: lines += ["", "## 4 结论", "全部通过,可以上线验收!" if ok else "存在未通过项,禁止上线。"]
    # 提示: return "\n".join(lines)
    raise NotImplementedError("t74-acceptance-s5 尚未实现:请按 TODO 提示完成复盘报告聚合")


def run_tests(work_dir):
    test_file = Path(work_dir) / "test_qa.py"
    names = "load_kb, retrieve, KB, p95, bench_retrieve, PERF_BUDGET_MS, run_checks, build_report, TEST_TOTAL"
    test_file.write_text(f"from __main__ import {names}\n" + TEST_CODE, encoding="utf-8")
    rc = pytest.main(["-q", "-o", "addopts=", "-p", "no:cacheprovider",
                      "--rootdir", str(work_dir), str(test_file)])
    return (TEST_TOTAL, TEST_TOTAL, 0) if rc == 0 else (TEST_TOTAL, 0, TEST_TOTAL)


def main():
    print("== 黑糖资料室 · 复盘与上线 s5 ==")
    backup = os.path.join(tempfile.gettempdir(), "kb_backup.json")
    Path(backup).write_text('{"kb": "黑糖资料室知识库备份"}', encoding="utf-8")
    with tempfile.TemporaryDirectory() as d:
        stats = run_tests(d)
        rp = os.path.join(d, "REPORT.md")
        perf_ms = p95(bench_retrieve(KB, "上线验收 故障", rounds=20)) * 1000
        report = build_report(stats, perf_ms, run_checks(KB, backup))
        Path(rp).write_text(report, encoding="utf-8")
        print(f"复盘报告已生成:{rp}")
    print("黑糖资料室,全部通过,可以上线!")


if __name__ == "__main__":
    main()
