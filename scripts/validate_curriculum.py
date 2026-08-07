#!/usr/bin/env python3
"""校验 curriculum.json 是否符合 Course schema,并做完整性检查。

检查项:
1. Pydantic Course 模型校验(字段类型/discriminated union)
2. id 唯一性(chapter/task/step)
3. 引用完整性(step.taskId 指向存在的 task, task.chapterId 指向存在的 chapter)
4. order 连续性
5. 解锁依赖的 prerequisite_task_ids 指向存在的 task
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))

from app.models.course import Course  # noqa: E402

CURRICULUM_PATH = _BACKEND / "app" / "data" / "curriculum.json"


def main() -> int:
    if not CURRICULUM_PATH.exists():
        print(f"错误: {CURRICULUM_PATH} 不存在, 请先运行 merge_curriculum.py")
        return 1

    with open(CURRICULUM_PATH, encoding="utf-8") as f:
        data = json.load(f)

    # 1. Pydantic 校验
    try:
        course = Course.model_validate(data)
    except Exception as e:
        print(f"❌ Pydantic 校验失败:\n{e}")
        return 1
    print("✓ Pydantic 校验通过")

    errors: list[str] = []

    # 收集所有 id
    chapter_ids = [c.id for c in course.chapters]
    task_ids = [t.id for c in course.chapters for t in c.tasks]
    step_ids = [s.id for c in course.chapters for t in c.tasks for s in t.steps]

    # 2. id 唯一性
    for name, ids in [("chapter", chapter_ids), ("task", task_ids), ("step", step_ids)]:
        dups = [x for x, n in Counter(ids).items() if n > 1]
        if dups:
            errors.append(f"重复 {name} id: {dups}")

    # 3. 引用完整性
    task_id_set = set(task_ids)
    chapter_id_set = set(chapter_ids)
    for c in course.chapters:
        for t in c.tasks:
            if t.chapter_id != c.id:
                errors.append(f"task {t.id} 的 chapterId={t.chapter_id} 与所在 chapter {c.id} 不一致")
            for s in t.steps:
                if s.task_id != t.id:
                    errors.append(f"step {s.id} 的 taskId={s.task_id} 与所在 task {t.id} 不一致")
            # 解锁前置
            for pre in c.unlock.prerequisite_task_ids:
                if pre not in task_id_set:
                    errors.append(f"chapter {c.id} 的前置 task {pre} 不存在")

    # 4. order 连续性(从 1 开始)
    for c in course.chapters:
        orders = [t.order for t in c.tasks]
        if orders != list(range(1, len(orders) + 1)):
            errors.append(f"chapter {c.id} 的 task order 不连续: {orders}")
        for t in c.tasks:
            sorders = [s.order for s in t.steps]
            if sorders and sorders != list(range(1, len(sorders) + 1)):
                errors.append(f"task {t.id} 的 step order 不连续: {sorders}")

    # 5. 每个 step 至少 1 条 validation
    for c in course.chapters:
        for t in c.tasks:
            for s in t.steps:
                if not s.validation:
                    errors.append(f"step {s.id} 没有 validation 规则")

    # 汇总
    print(f"\n课程: {course.title} v{course.version}")
    print(f"  章节 {len(course.chapters)}, 任务 {len(task_ids)}, 步骤 {len(step_ids)}")
    print(f"  总经验 {course.total_exp}")

    if errors:
        print(f"\n❌ 发现 {len(errors)} 个问题:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\n✅ 全部校验通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
