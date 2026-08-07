#!/usr/bin/env python3
"""课程生成器(分段式) —— 逐个 step 调 LLM 生成,避免长输出超时/漏字段。

工作流:
1. 读 curriculum_outline.yaml + system_prompt.txt
2. 遍历每个 task, 逐个 step 调 LLM 生成(每次只生成 1 个 step)
3. 单 step Pydantic 校验, 失败重试 3 次
4. 全部 step 成功 → 保存 {steps: [...]}, 标记 completed
5. 断点续传(.generate_progress.json), 最后 merge + validate

用法:
  python scripts/generate_curriculum.py                    # 生成全部未完成
  python scripts/generate_curriculum.py --task-id t01      # 单 task
  python scripts/generate_curriculum.py --chapter-id ch02  # 单章
  python scripts/generate_curriculum.py --force            # 忽略进度, 重新生成
  python scripts/generate_curriculum.py --merge-only       # 只合并不生成
  python scripts/generate_curriculum.py --validate-only    # 只校验
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import yaml
from openai import OpenAI
from pydantic import BaseModel, ValidationError

# 让脚本能 import 后端 app 包(脚本在 scripts/, 后端在 backend/)
_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))

from app.config import settings  # noqa: E402
from app.models.course import Step  # noqa: E402

# === 路径 ===
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
OUTLINE_PATH = SCRIPTS_DIR / "curriculum_outline.yaml"
PROMPTS_DIR = SCRIPTS_DIR / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system_prompt.txt"
DATA_DIR = _BACKEND / "app" / "data"
CHAPTERS_DIR = DATA_DIR / "chapters"
PROGRESS_PATH = PROJECT_ROOT / ".generate_progress.json"

# === 生成参数(分段式: 单 step 短输出) ===
MAX_RETRIES = 2  # 减少重试, 快速跳过超时 task
TEMPERATURES = [0.7, 0.3]
MAX_TOKENS = 1800  # 降输出量, Qwen 生成更快(~50秒), 不易超时
TIMEOUT = 90  # 快速超时, 不浪费3分钟等

# 单 step 字段结构提示(附到 prompt 让 LLM 遵循)
SCHEMA_HINT = """
## 输出 JSON 结构(严格遵循, camelCase)
顶层: {"step": {...}}
step 字段:
  - id(string), taskId(string), order(int), title(string)
  - instruction(string, 中文 markdown, 200-400字, 含目标/概念/操作指引)
  - starterCode(string, 含 # TODO: 注释占位)
  - solutionCode(string, 完整可运行答案)
  - hints(数组, 每条 {order:int, text:string, costExp:int}, 3条由浅入深)
  - codeSamples(数组, 每条 {title, language:'python'|'bash'|'text', code, description?})
  - terms(数组, 每条 {name, definition, referenceUrl?})
  - techStack(数组, 每条 {name, role, description, officialUrl})
  - validation(数组, 至少2条, 每条 {type, message, blocking?, ...type对应字段})
validation.type 可选:
  api_call_exists(+api,minCount?), placeholder_filled(+placeholder),
  regex_in_code(+pattern,flags?), output_contains(+text,caseSensitive?),
  output_matches(+pattern,flags?), output_equals(+expected,trim?,ignoreCase?),
  ast_structure(+astType,name?,minCount?), unit_test(+testCode),
  sandbox_run(+expectedStdout?,stderrMustBeEmpty?,expectedExitCode?)
示例: {"step":{"id":"t01-s1","taskId":"t01","order":1,"title":"...",
  "instruction":"...","starterCode":"...","solutionCode":"...",
  "hints":[{"order":1,"text":"...","costExp":2}],
  "codeSamples":[],"terms":[],"techStack":[],
  "validation":[{"type":"placeholder_filled","message":"...","placeholder":"# TODO:"}]}}"""


class StepOutput(BaseModel):
    """单个 step 的 LLM 输出容器。"""

    step: Step


def load_outline() -> dict:
    with open(OUTLINE_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def build_step_prompt(
    chapter: dict, task: dict, step_order: int, step_count: int, defaults: dict
) -> str:
    """构造单 step 的 user prompt。"""
    step_id = f"{task['id']}-s{step_order}"
    needs_sandbox = task.get("needs_sandbox", defaults.get("needs_sandbox", False))
    needs_network = task.get("needs_network", defaults.get("needs_network", False))
    network_hint = (
        "可调真实 API(假设 OPENAI_API_KEY 已配置)"
        if needs_network
        else "不要调真实 API, 用 mock 或本地数据演示"
    )
    return f"""请为以下学习任务生成第 {step_order}/{step_count} 个步骤(step)。

## 任务信息
- 章节: {chapter['title']} ({chapter['id']})
- 任务: {task['title']} ({task['id']})
- 难度: {task['difficulty']}
- 需要沙箱运行: {needs_sandbox}
- 需要联网: {needs_network}

## 任务主题(本任务要教什么)
{task['topic']}

## 本步骤要求
- 这是第 {step_order} 个 step(共 {step_count} 个), 内容应循序渐进(第1步基础, 后续递进)。
- id: {step_id}
- taskId: {task['id']}
- order: {step_order}
- title: 本步骤标题(简短)
- instruction: 中文 markdown, 200-400字, 含目标/概念解释/操作指引。
- starterCode: 含 # TODO: 占位, 标注学习者填什么, 其余给可运行上下文。
- solutionCode: 完整可运行答案(替换 TODO)。{network_hint}。
- hints: 3条, 由浅入深, 每条 {{order, text, costExp}}。
- codeSamples: 1-2 个相关示例(不是答案)。
- terms: 2-4 个核心术语。
- techStack: 1-3 个用到的库/工具。
- validation: 至少2条(至少1条 blocking=true)。
- 严格输出 JSON, 不要任何额外文字。
{SCHEMA_HINT}"""


def get_client() -> OpenAI:
    if not settings.openai_api_key or settings.openai_api_key == "sk-...":
        raise SystemExit(
            "错误: OPENAI_API_KEY 未配置。\n"
            "请复制 .env.example 为 .env 并填入你的 API key, 再运行本脚本。"
        )
    return OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


def call_llm_for_step(client: OpenAI, system_prompt: str, user_prompt: str) -> dict | None:
    """调 LLM 生成单个 step, 返回 step dict。失败返回 None。"""
    for attempt, temp in enumerate(TEMPERATURES):
        try:
            resp = client.chat.completions.create(
                model=settings.generator_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temp,
                max_tokens=MAX_TOKENS,
                timeout=TIMEOUT,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            if not content:
                raise ValueError("LLM 返回空内容")
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                from json_repair import repair_json

                data = json.loads(repair_json(content))
            # 归一化: LLM 可能直接输出 step 对象(含 id)而非 {step: {...}}
            if isinstance(data, dict) and "step" not in data and "id" in data:
                data = {"step": data}
            StepOutput.model_validate(data)
            return data["step"]
        except ValidationError as e:
            print(f"    [重试 {attempt + 1}/{MAX_RETRIES}] 校验失败: {str(e)[:150]}")
        except Exception as e:
            print(f"    [重试 {attempt + 1}/{MAX_RETRIES}] 调用失败: {type(e).__name__}: {str(e)[:150]}")
        if attempt < MAX_RETRIES - 1:
            time.sleep(2)
    return None


def save_task_steps(chapter_id: str, task_id: str, steps: list[dict]) -> Path:
    """保存单 task 的 steps JSON。"""
    out_dir = CHAPTERS_DIR / chapter_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{task_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"steps": steps}, f, ensure_ascii=False, indent=2)
    return out_path


def load_progress() -> dict:
    if PROGRESS_PATH.exists():
        return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    return {"completed": [], "failed": [], "version": "1.0"}


def save_progress(progress: dict) -> None:
    PROGRESS_PATH.write_text(
        json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def collect_tasks(outline: dict, args) -> tuple[list[tuple[dict, dict]], dict]:
    defaults = outline.get("defaults", {})
    result = []
    for chapter in outline["chapters"]:
        if args.chapter_id and chapter["id"] != args.chapter_id:
            continue
        for task in chapter["tasks"]:
            if args.task_id and task["id"] != args.task_id:
                continue
            result.append((chapter, task))
    return result, defaults


def run_generate(args) -> int:
    outline = load_outline()
    system_prompt = load_system_prompt()
    tasks, defaults = collect_tasks(outline, args)

    progress = (
        {"completed": [], "failed": [], "version": "1.0"}
        if args.force
        else load_progress()
    )

    tasks_to_gen = [
        (ch, tk)
        for ch, tk in tasks
        if tk["id"] not in progress["completed"]
        and (args.force or tk["id"] not in progress["failed"])
    ]

    if not tasks_to_gen:
        print("没有待生成的 task(全部已完成)。")
        return run_merge()

    client = get_client()
    print(f"待生成 {len(tasks_to_gen)} 个 task(分段式: 逐 step 生成)...\n")
    success = 0
    for i, (chapter, task) in enumerate(tasks_to_gen, 1):
        step_count = task.get("steps", defaults["steps_per_task"])
        print(f"[{i}/{len(tasks_to_gen)}] {task['id']} — {task['title']} ({step_count} steps)")
        steps: list[dict] = []
        task_ok = True
        for step_order in range(1, step_count + 1):
            user_prompt = build_step_prompt(chapter, task, step_order, step_count, defaults)
            step = call_llm_for_step(client, system_prompt, user_prompt)
            if step is None:
                print(f"  step {step_order} 生成失败, 跳过该 task")
                task_ok = False
                break
            steps.append(step)
            print(f"  step {step_order}/{step_count} ✓")
            time.sleep(1)  # step 间防限流

        if task_ok:
            path = save_task_steps(chapter["id"], task["id"], steps)
            print(f"  已保存 {path.relative_to(PROJECT_ROOT)}\n")
            progress["completed"].append(task["id"])
            if task["id"] in progress["failed"]:
                progress["failed"].remove(task["id"])
            save_progress(progress)
            success += 1
        else:
            if task["id"] not in progress["failed"]:
                progress["failed"].append(task["id"])
            save_progress(progress)
        time.sleep(2)  # task 间防限流

    print(f"\n生成完成: {success}/{len(tasks_to_gen)} 成功, {len(progress['failed'])} 失败")
    if progress["failed"]:
        print(f"失败 task: {progress['failed']}")
    return run_merge()


def run_merge() -> int:
    print("=== 合并 curriculum.json ===")
    merge_script = SCRIPTS_DIR / "merge_curriculum.py"
    if not merge_script.exists():
        print("merge_curriculum.py 不存在, 跳过")
        return 0
    import subprocess

    r = subprocess.run([sys.executable, str(merge_script)], check=False)
    return r.returncode


def run_validate() -> int:
    print("=== 校验课程 ===")
    validate_script = SCRIPTS_DIR / "validate_curriculum.py"
    if not validate_script.exists():
        print("validate_curriculum.py 不存在, 跳过")
        return 0
    import subprocess

    r = subprocess.run([sys.executable, str(validate_script)], check=False)
    return r.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="生成课程内容(分段式, 调 LLM)")
    parser.add_argument("--task-id", help="只生成指定 task")
    parser.add_argument("--chapter-id", help="只生成指定章节")
    parser.add_argument("--force", action="store_true", help="忽略进度, 重新生成")
    parser.add_argument("--merge-only", action="store_true", help="只合并不生成")
    parser.add_argument("--validate-only", action="store_true", help="只校验不生成")
    args = parser.parse_args()

    if args.validate_only:
        return run_validate()
    if args.merge_only:
        return run_merge()
    return run_generate(args)


if __name__ == "__main__":
    sys.exit(main())
