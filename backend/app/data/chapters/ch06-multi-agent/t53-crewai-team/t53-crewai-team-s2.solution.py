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

    description: str
    expected_output: str
    role: str
    context: list = field(default_factory=list)


def build_plan() -> list[Task]:
    """天庭作战图:四道军令,顺序即依赖顺序。"""
    return [
        Task(
            description="需求分析:调研用户诉求,产出需求文档与功能清单",
            expected_output="一份需求文档,列出至少 3 个核心功能",
            role="产品经理",
        ),
        Task(
            description="API 设计:依据需求文档设计接口契约与数据模型",
            expected_output="接口设计文档,含路径、参数与响应示例",
            role="后端工程师",
            context=["需求文档"],
        ),
        Task(
            description="前端开发:按接口文档实现页面并与 API 联调",
            expected_output="可运行的界面,展示真实接口数据",
            role="前端工程师",
            context=["接口设计文档"],
        ),
        Task(
            description="测试验收:设计用例覆盖核心功能,输出验收结论",
            expected_output="测试报告,标注通过/失败的用例清单",
            role="测试工程师",
            context=["需求文档", "界面"],
        ),
    ]


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
