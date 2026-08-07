"""课程数据缓存(启动时加载 curriculum.json 到内存索引, 零 IO 查询)。"""
from __future__ import annotations

import json
from pathlib import Path

from app.models.course import Chapter, Course, Step, Task


class CurriculumCache:
    """课程数据单例缓存, 启动时 load 一次, 所有 API 读内存。"""

    _course: Course | None = None
    _task_index: dict[str, Task] = {}
    _chapter_index: dict[str, Chapter] = {}
    _step_index: dict[str, Step] = {}

    @classmethod
    def load(cls, data_dir: Path) -> None:
        """启动时调用一次, 读取 curriculum.json 并建索引。"""
        curriculum_path = data_dir / "curriculum.json"
        if not curriculum_path.exists():
            raise FileNotFoundError(f"课程数据不存在: {curriculum_path}, 请先运行生成器")
        course_data = json.loads(curriculum_path.read_text(encoding="utf-8"))
        course = Course.model_validate(course_data)
        cls._course = course
        cls._task_index = {}
        cls._chapter_index = {}
        cls._step_index = {}
        for ch in course.chapters:
            cls._chapter_index[ch.id] = ch
            for t in ch.tasks:
                cls._task_index[t.id] = t
                for s in t.steps:
                    cls._step_index[s.id] = s

    @classmethod
    def get_course(cls) -> Course | None:
        return cls._course

    @classmethod
    def get_chapter(cls, chapter_id: str) -> Chapter | None:
        return cls._chapter_index.get(chapter_id)

    @classmethod
    def get_task(cls, task_id: str) -> Task | None:
        return cls._task_index.get(task_id)

    @classmethod
    def get_step(cls, step_id: str) -> Step | None:
        return cls._step_index.get(step_id)

    @classmethod
    def is_loaded(cls) -> bool:
        return cls._course is not None
