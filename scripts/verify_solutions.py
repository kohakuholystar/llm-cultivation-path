#!/usr/bin/env python3
"""课程质量门：对 curriculum.json 里每个 step 做静态检查 + 沙箱实跑验证。

用法:
    python scripts/verify_solutions.py                  # 全部检查（含沙箱实跑）
    python scripts/verify_solutions.py --chapter ch01   # 只查某章（按章 id 前缀匹配）
    python scripts/verify_solutions.py --static-only    # 只做静态检查，不跑沙箱
    python scripts/verify_solutions.py --workers 6      # 沙箱并发数（默认 4）

静态检查（每个 step）:
    - instruction ≥300 字；solutionCode 非空行 40~120（<40 fail，>120 warn）
    - starterCode 含 # TODO；solutionCode 不含 # TODO
    - hints ≥2、codeSamples ≥1、terms ≥2、techStack ≥1
    - validation ≥2 条且 ≥1 条 blocking
    - GPT 残留（gpt-4/gpt-3/api.openai.com/chatgpt，不区分大小写）
    - U+FFFD 替换符
    - validation 规则与 solutionCode 对齐：
        api_call_exists / regex_in_code / ast_structure（用真 ast 解析）

沙箱实跑（needsNetwork 任务的 step 跳过，仅静态检查）:
    - docker run llmquest-sandbox:latest，要求 exitCode == 0、30s 内完成
    - 复核 sandbox_run / output_contains / output_matches / output_equals 规则
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
CURRICULUM_PATH = _PROJECT_ROOT / "backend" / "app" / "data" / "curriculum.json"
SANDBOX_IMAGE = "llmquest-sandbox:latest"
RUN_TIMEOUT = 30

GPT_RESIDUE = re.compile(r"gpt-?[34]|api\.openai\.com|chatgpt", re.IGNORECASE)


class StepReport:
    def __init__(self, step_id: str):
        self.step_id = step_id
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.skipped_run = False

    def fail(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


# ---------- 静态检查 ----------

def ast_names(code: str) -> dict[str, list[str]]:
    """用真 ast 收集定义/引用名（模拟前端 astLite 的判定范围）。"""
    names: dict[str, list[str]] = {k: [] for k in (
        "function_def", "async_function_def", "class_def", "import", "import_from", "call", "assign")}
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            names["async_function_def"].append(node.name)
            names["function_def"].append(node.name)  # 前端 astLite 类内方法也算 function_def
        elif isinstance(node, ast.FunctionDef):
            names["function_def"].append(node.name)
        elif isinstance(node, ast.ClassDef):
            names["class_def"].append(node.name)
        elif isinstance(node, ast.Import):
            names["import"].extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            names["import_from"].append(node.module or "")
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                names["call"].append(f.id)
            elif isinstance(f, ast.Attribute):
                names["call"].append(f.attr)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name):
                    names["assign"].append(t.id)
    return names


def name_match(candidates: list[str], want: str) -> bool:
    return any(c == want or c.startswith(want + ".") or want.startswith(c + ".") for c in candidates)


def check_static(step: dict, rep: StepReport) -> None:
    sid = step["id"]
    instruction = step.get("instruction", "")
    starter = step.get("starterCode", "")
    solution = step.get("solutionCode", "")

    if len(instruction) < 300:
        rep.fail(f"instruction 仅 {len(instruction)} 字（要求 ≥300）")

    sol_lines = [l for l in solution.splitlines() if l.strip()]
    if len(sol_lines) < 40:
        rep.fail(f"solutionCode 仅 {len(sol_lines)} 非空行（要求 ≥40，目标 50-100）")
    elif len(sol_lines) > 120:
        rep.warn(f"solutionCode {len(sol_lines)} 行，偏长（目标 50-100）")

    if "# TODO" not in starter:
        rep.fail("starterCode 缺少 # TODO")
    if "# TODO" in solution:
        rep.fail("solutionCode 不应残留 # TODO")

    if len(step.get("hints", [])) < 2:
        rep.fail("hints 少于 2 条")
    if not step.get("codeSamples"):
        rep.fail("缺少 codeSamples")
    if len(step.get("terms", [])) < 2:
        rep.fail("terms 少于 2 个")
    if not step.get("techStack"):
        rep.fail("缺少 techStack")

    rules = step.get("validation", [])
    if len(rules) < 2:
        rep.fail(f"validation 仅 {len(rules)} 条（要求 ≥2）")
    if not any(r.get("blocking", True) for r in rules):
        rep.fail("validation 没有 blocking 规则")

    blob = json.dumps(step, ensure_ascii=False)
    if "\ufffd" in blob:
        rep.fail("存在 U+FFFD 替换符")
    if GPT_RESIDUE.search(blob):
        rep.fail("存在 GPT/OpenAI 官方残留（应统一 DeepSeek）")

    # validation 规则与 solutionCode 对齐（静态规则）
    names = ast_names(solution)
    for i, r in enumerate(rules):
        t = r.get("type")
        tag = f"规则[{i}]({t})"
        if t == "api_call_exists":
            api = re.escape(r["api"])
            cnt = len(re.findall(api, solution))
            if cnt < r.get("minCount", 1):
                rep.fail(f"{tag} solutionCode 中未找到 {r['api']} ×{r.get('minCount', 1)}")
        elif t == "regex_in_code":
            try:
                if not re.search(r["pattern"], solution, _flags(r.get("flags"))):
                    rep.fail(f"{tag} pattern 在 solutionCode 中不匹配")
            except re.error as e:
                rep.fail(f"{tag} 非法正则: {e}")
        elif t == "ast_structure":
            want_type = r["astType"]
            candidates = names.get(want_type, [])
            if r.get("name"):
                if not name_match(candidates, r["name"]):
                    rep.fail(f"{tag} solutionCode 无 {want_type} 名为 {r['name']}（实际: {candidates or '无'}）")
            elif len(candidates) < r.get("minCount", 1):
                rep.fail(f"{tag} solutionCode 中 {want_type} 数量不足")
        elif t == "placeholder_filled":
            pass  # solution 无 TODO 即天然满足（上面已查）
        elif t == "unit_test":
            rep.warn(f"{tag} unit_test 需后端合并 testCode，本脚本仅查 exitCode")


def _flags(flags: str | None) -> int:
    m = 0
    if flags:
        if "i" in flags:
            m |= re.IGNORECASE
        if "m" in flags:
            m |= re.MULTILINE
        if "s" in flags:
            m |= re.DOTALL
    return m


# ---------- 沙箱实跑 ----------

def docker_available() -> bool:
    try:
        subprocess.run(["docker", "image", "inspect", SANDBOX_IMAGE],
                       capture_output=True, timeout=10, check=True)
        return True
    except Exception:
        return False


def run_in_sandbox(code: str, timeout: int = RUN_TIMEOUT) -> dict:
    cmd = [
        "docker", "run", "--rm", "-i",
        "--network=none", "--memory=256m", "--cpus=0.5",
        "--read-only", "--tmpfs=/tmp:rw,size=10m",
        SANDBOX_IMAGE,
        "python", "-c", "import sys; exec(sys.stdin.read())",
    ]
    try:
        p = subprocess.run(cmd, input=code.encode("utf-8"), capture_output=True, timeout=timeout)
        return {"stdout": p.stdout.decode("utf-8", "replace"), "stderr": p.stderr.decode("utf-8", "replace"),
                "exitCode": p.returncode, "timedOut": False}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "", "exitCode": -1, "timedOut": True}
    except Exception as e:  # docker 不可用等
        return {"stdout": "", "stderr": str(e), "exitCode": -1, "timedOut": False}


def check_run(step: dict, rep: StepReport) -> None:
    out = run_in_sandbox(step["solutionCode"])
    if out["timedOut"]:
        rep.fail(f"沙箱执行超时（>{RUN_TIMEOUT}s）")
        return
    if out["exitCode"] != 0:
        tail = "\n".join(out["stderr"].splitlines()[-5:])
        rep.fail(f"沙箱执行失败 exitCode={out['exitCode']}: {tail}")
        return

    stdout = out["stdout"]
    for i, r in enumerate(step.get("validation", [])):
        t = r.get("type")
        tag = f"规则[{i}]({t})"
        if t == "sandbox_run":
            if r.get("stderrMustBeEmpty") and out["stderr"].strip():
                rep.fail(f"{tag} stderr 非空: {out['stderr'][:200]}")
            if "expectedExitCode" in r and r["expectedExitCode"] is not None \
                    and out["exitCode"] != r["expectedExitCode"]:
                rep.fail(f"{tag} exitCode {out['exitCode']} != {r['expectedExitCode']}")
            if r.get("expectedStdout"):
                pat = r["expectedStdout"]
                try:
                    ok = re.search(pat, stdout) is not None
                except re.error:
                    ok = stdout.strip() == pat.strip()
                if not ok:
                    rep.fail(f"{tag} stdout 不匹配 /{pat}/，实际输出: {stdout[:200]!r}")
        elif t == "output_contains":
            text = r["text"]
            hay = stdout if r.get("caseSensitive", True) else stdout.lower()
            needle = text if r.get("caseSensitive", True) else text.lower()
            if needle not in hay:
                rep.fail(f"{tag} stdout 不含 {text!r}")
        elif t == "output_matches":
            if not re.search(r["pattern"], stdout, _flags(r.get("flags"))):
                rep.fail(f"{tag} stdout 不匹配 /{r['pattern']}/")
        elif t == "output_equals":
            a, b = stdout, r["expected"]
            if r.get("trim", True):
                a, b = a.strip(), b.strip()
            if r.get("ignoreCase"):
                a, b = a.lower(), b.lower()
            if a != b:
                rep.fail(f"{tag} stdout != expected")


# ---------- 主流程 ----------

def iter_steps(course: dict, chapter_filter: str | None):
    for ch in course["chapters"]:
        if chapter_filter and not ch["id"].startswith(chapter_filter):
            continue
        for task in ch["tasks"]:
            for step in task["steps"]:
                yield ch, task, step


def main() -> int:
    # Windows GBK 控制台兼容
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", help="只检查某章（前缀匹配，如 ch01）")
    ap.add_argument("--static-only", action="store_true", help="不跑沙箱")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--file", default=str(CURRICULUM_PATH), help="curriculum.json 路径")
    args = ap.parse_args()

    course = json.loads(Path(args.file).read_text(encoding="utf-8"))
    items = list(iter_steps(course, args.chapter))
    if not items:
        print("没有匹配的 step")
        return 1

    can_run = not args.static_only and docker_available()
    if not args.static_only and not can_run:
        print("警告: 沙箱镜像不可用，降级为仅静态检查（先 docker info / pnpm build:sandbox）")

    reports: list[StepReport] = []

    def process(item) -> StepReport:
        ch, task, step = item
        rep = StepReport(step["id"])
        check_static(step, rep)
        if can_run:
            if task.get("needsNetwork"):
                rep.skipped_run = True  # 联网步不消耗 key，仅静态检查
            else:
                check_run(step, rep)
        return rep

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for rep in ex.map(process, items):
            reports.append(rep)
            status = "✓" if not rep.errors else "✗"
            extra = " [跳过实跑:联网]" if rep.skipped_run else ""
            print(f"{status} {rep.step_id}{extra}")
            for m in rep.errors:
                print(f"    ERROR: {m}")
            for m in rep.warnings:
                print(f"    warn : {m}")

    n_err = sum(1 for r in reports if r.errors)
    n_warn = sum(1 for r in reports if r.warnings)
    n_skip = sum(1 for r in reports if r.skipped_run)
    print(f"\n共 {len(reports)} 步: {len(reports)-n_err} 通过, {n_err} 失败, {n_warn} 有警告, {n_skip} 联网步仅静态检查")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
