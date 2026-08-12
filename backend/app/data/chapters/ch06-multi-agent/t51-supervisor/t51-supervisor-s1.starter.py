"""校园 AI 社 · s1:任务契约与分派策略

社长在项目工作台统一协调,把一份需求文档拆成一张张任务单,按社团成员专长分派。
本步定义协作的语言——任务单 AgentTask 与完工汇报 TaskResult,
再用关键词路由表把任务分给前端、后端、测试、文档四位社团成员。
"""


# === 学习契约（面向学生）===
# 本节目标：LangGraph 前置：任务契约与分派策略。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `route_task(task: AgentTask) -> str`：输入为签名中的参数；输出为 `str`。用途：按标题关键词匹配路由表;匹配不到落给后端同学。
#   - `assign_tasks(requests: list[str]) -> list[AgentTask]`：输入为签名中的参数；输出为 `list[AgentTask]`。用途：把需求文档拆成任务单并分派,返回带负责人的任务单列表。
#   - `specialist_work(task: AgentTask) -> TaskResult`：输入为签名中的参数；输出为 `TaskResult`。用途：社团成员开工:按专长产出模拟成果,写成完工汇报。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `AgentTask`：承载本节状态/数据；重点方法：见类定义。
#   - `TaskResult`：承载本节状态/数据；重点方法：见类定义。
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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


# 关键词路由表:按任务标题里的关键词决定派给哪位社团成员
SKILL_ROUTES = [
    (("前端", "页面", "界面"), "前端同学"),
    (("接口", "后端", "服务"), "后端同学"),
    (("测试", "用例"), "测试同学"),
    (("文档", "说明"), "文档同学"),
]


def route_task(task: AgentTask) -> str:
    """按标题关键词匹配路由表;匹配不到落给后端同学。"""
    # TODO: 遍历 SKILL_ROUTES,关键词命中即返回对应社团成员,循环结束兜底后端同学
    # 提示: for keywords, assignee in SKILL_ROUTES:
    #           if any(k in task.title for k in keywords):
    #               return assignee
    #       return "后端同学"
    raise NotImplementedError("t51-supervisor-s1 尚未实现:请按 TODO 提示补齐 route_task 路由")


def assign_tasks(requests: list[str]) -> list[AgentTask]:
    """把需求文档拆成任务单并分派,返回带负责人的任务单列表。"""
    tasks = []
    for i, req in enumerate(requests, start=1):
        task = AgentTask(id=f"t{i}", title=req)
        task.assignee = route_task(task)
        tasks.append(task)
    return tasks


def specialist_work(task: AgentTask) -> TaskResult:
    """社团成员开工:按专长产出模拟成果,写成完工汇报。"""
    # TODO: 按 assignee 分四支产出模拟成果,统一构造 TaskResult 交卷
    # 提示: if task.assignee == "前端同学": data = f"已产出页面骨架: {task.title}"
    #       elif task.assignee == "测试同学": data = f"已编写测试用例 {len(task.title)} 条,全部通过"
    #       elif task.assignee == "文档同学": data = f"文档已更新: {task.title}"
    #       else: data = f"后端接口已就绪: {task.title}"
    #       return TaskResult(task_id=task.id, assignee=task.assignee, ok=True, data=data)
    raise NotImplementedError("t51-supervisor-s1 尚未实现:请按 TODO 提示补齐 specialist_work 开工")


def main() -> None:
    requests = ["前端页面设计", "后端接口联调", "登录模块测试", "接口使用文档"]
    tasks = assign_tasks(requests)
    print("== 校园 AI 社任务分派 ==")
    for t in tasks:
        print(f"  {t.id} {t.title} -> {t.assignee}")
    print("== 社团成员开工 ==")
    for t in tasks:
        r = specialist_work(t)
        print(f"  [{r.assignee}] {r.data}")


if __name__ == "__main__":
    main()
