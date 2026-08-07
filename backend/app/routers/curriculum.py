"""课程数据查询 API。"""
from fastapi import APIRouter, HTTPException

from app.services.curriculum_loader import CurriculumCache

router = APIRouter(prefix="/api", tags=["course"])


@router.get("/course")
async def get_course():
    """完整课程树(含所有 chapter/task/step)。"""
    course = CurriculumCache.get_course()
    if course is None:
        raise HTTPException(503, "课程数据未加载")
    return course


@router.get("/course/{chapter_id}")
async def get_chapter(chapter_id: str):
    """单章节详情。"""
    ch = CurriculumCache.get_chapter(chapter_id)
    if ch is None:
        raise HTTPException(404, f"章节 {chapter_id} 不存在")
    return ch


@router.get("/task/{task_id}")
async def get_task(task_id: str):
    """任务详情(含 step 全字段, 含 solutionCode)。"""
    t = CurriculumCache.get_task(task_id)
    if t is None:
        raise HTTPException(404, f"任务 {task_id} 不存在")
    return t


@router.get("/task/{task_id}/solution")
async def get_solution(task_id: str, stepId: str | None = None):
    """获取参考答案。"""
    t = CurriculumCache.get_task(task_id)
    if t is None:
        raise HTTPException(404, f"任务 {task_id} 不存在")
    if stepId:
        s = CurriculumCache.get_step(stepId)
        if s is None:
            raise HTTPException(404, f"步骤 {stepId} 不存在")
        return {"stepId": stepId, "solutionCode": s.solution_code}
    return {
        "taskId": task_id,
        "steps": [{"stepId": s.id, "solutionCode": s.solution_code} for s in t.steps],
    }
