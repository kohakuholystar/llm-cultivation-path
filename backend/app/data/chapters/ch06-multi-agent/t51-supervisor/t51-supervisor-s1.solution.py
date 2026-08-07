"""天庭 · s1:任务契约与分派策略

玉帝坐镇凌霄殿,把一卷诏书拆成一张张任务单,按仙官专长分派。
本步定义协作的语言——任务单 AgentTask 与完工汇报 TaskResult,
再用关键词路由表把任务分给前端、后端、测试、文档四位仙官。
"""
from dataclasses import dataclass


@dataclass
class AgentTask:
    """一张任务单:编号、标题、负责人、载荷。"""
    id: str
    title: str
    assignee: str = ""
    payload: str = ""


@dataclass
class TaskResult:
    """一张完工汇报:谁干的、干成了没、交出了什么。"""
    task_id: str
    assignee: str
    ok: bool
    data: str = ""


# 关键词路由表:按任务标题里的关键词决定派给哪位仙官
SKILL_ROUTES = [
    (("前端", "页面", "界面"), "前端仙官"),
    (("接口", "后端", "服务"), "后端仙官"),
    (("测试", "用例"), "测试仙官"),
    (("文档", "说明"), "文档仙官"),
]


def route_task(task: AgentTask) -> str:
    """按标题关键词匹配路由表;匹配不到落给后端仙官。"""
    for keywords, assignee in SKILL_ROUTES:
        if any(k in task.title for k in keywords):
            return assignee
    return "后端仙官"


def assign_tasks(requests: list[str]) -> list[AgentTask]:
    """把诏书拆成任务单并分派,返回带负责人的任务单列表。"""
    tasks = []
    for i, req in enumerate(requests, start=1):
        task = AgentTask(id=f"t{i}", title=req)
        task.assignee = route_task(task)
        tasks.append(task)
    return tasks


def specialist_work(task: AgentTask) -> TaskResult:
    """仙官开工:按专长产出模拟成果,写成完工汇报。"""
    if task.assignee == "前端仙官":
        data = f"已产出页面骨架: {task.title}"
    elif task.assignee == "测试仙官":
        data = f"已编写测试用例 {len(task.title)} 条,全部通过"
    elif task.assignee == "文档仙官":
        data = f"文档已更新: {task.title}"
    else:
        data = f"后端接口已就绪: {task.title}"
    return TaskResult(task_id=task.id, assignee=task.assignee, ok=True, data=data)


def main() -> None:
    requests = ["前端页面设计", "后端接口联调", "登录模块测试", "接口使用文档"]
    tasks = assign_tasks(requests)
    print("== 天庭点将 ==")
    for t in tasks:
        print(f"  {t.id} {t.title} -> {t.assignee}")
    print("== 仙官开工 ==")
    for t in tasks:
        r = specialist_work(t)
        print(f"  [{r.assignee}] {r.data}")


if __name__ == "__main__":
    main()
