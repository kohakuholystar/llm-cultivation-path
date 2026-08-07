"""天庭 · s2:排兵布阵,Task 任务清单成形

角色卡就位后,本步为天庭排兵布阵:定义任务实体 Task,
把四道军令组成一张按依赖顺序排列的作战图,复刻 CrewAI 的 Task。
"""

from dataclasses import dataclass, field


@dataclass
class Agent:
    """角色卡:role 你是谁,goal 要达成什么,backstory 立场与专长。"""

    role: str
    goal: str
    backstory: str


def build_heaven() -> list[Agent]:
    """天庭班子:四位执行神职。"""
    return [
        Agent("产品经理", "把用户诉求翻译成清晰需求", "凡间走一遭,最懂用户要什么。"),
        Agent("后端工程师", "把需求落成可靠接口", "内务府执笔,契约先行,数据为王。"),
        Agent("前端工程师", "把接口画成可用界面", "凌云殿画师,像素与交互皆精。"),
        Agent("测试工程师", "把风险挡在上线之前", "雷部判官,专门挑刺。"),
    ]


@dataclass
class Task:
    """军令:干什么、验收标准、交给谁、依赖什么。"""
    # TODO: 定义四个字段:description / expected_output / role 为 str,context 声明前置依赖
    # 提示: 无默认值字段在前;context: list = field(default_factory=list)
    pass


def build_plan() -> list[Task]:
    """天庭作战图:四道军令,顺序即依赖顺序。"""
    # TODO: 返回 4 个按依赖顺序排列的 Task,后三道写明 context 依赖
    # 提示: Task(description=..., expected_output=..., role=..., context=[...])
    raise NotImplementedError("build_plan 尚未实现:请按 TODO 提示返回 4 个 Task(...) 组成的列表")


def show_plan(plan: list[Task]) -> None:
    """把作战图渲染成可读的军令清单。"""
    for i, task in enumerate(plan, 1):
        deps = "、".join(task.context) if task.context else "无"
        print(f"军令 {i}:{task.description}")
        print(f"  执行者:{task.role}")
        print(f"  验收标准:{task.expected_output}")
        print(f"  依赖:{deps}")


def main() -> None:
    print("== 天庭作战图 ==")
    show_plan(build_plan())


if __name__ == "__main__":
    main()
