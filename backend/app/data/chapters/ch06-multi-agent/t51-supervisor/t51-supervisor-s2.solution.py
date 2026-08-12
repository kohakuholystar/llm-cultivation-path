"""校园 AI 社 · s2:使用 LangGraph 的节点与边

上一张任务单已经能分派,本步直接使用 LangGraph 的 StateGraph:
节点是普通函数,边决定流转方向;条件边由 router 函数看状态选路。
最后用一张校园 AI 社小图把「拆需求 -> 派活 -> 汇报」串起来跑通。
"""
from dataclasses import dataclass
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


@dataclass
class AgentTask:
    """一张任务单。"""
    id: str
    title: str
    assignee: str = ""
    payload: str = ""


@dataclass
class TaskResult:
    """一张完工汇报。"""
    task_id: str
    assignee: str
    ok: bool
    data: str = ""


class WorkflowState(TypedDict, total=False):
    request: str
    tasks: list[AgentTask]
    results: list[TaskResult]


def spot_node(state: dict) -> dict:
    """任务分派:把需求文档按「和」拆成任务单,分派给对应社团成员。"""
    request = state["request"]
    tasks = [AgentTask(id=f"t{i}", title=t, assignee="前端同学" if "前端" in t else "后端同学")
             for i, t in enumerate(request.split("和"), start=1)]
    return {"tasks": tasks}


def work_node(state: dict) -> dict:
    """开工:每张任务单产出完工汇报。"""
    results = [TaskResult(task_id=t.id, assignee=t.assignee, ok=True,
                          data=f"已完成「{t.title}」") for t in state["tasks"]]
    return {"results": results}


def router_after_work(state: dict) -> str:
    """完工检查:有汇报就去汇报,没有就返工。"""
    return "finish" if state.get("results") else "rework"


def rework_node(state: dict) -> dict:
    """兜底返工:补一张通用任务单,重新开工。"""
    state["tasks"].append(AgentTask(id="t9", title="补充通用任务", assignee="后端同学"))
    return {}


def main() -> None:
    builder = StateGraph(WorkflowState)
    builder.add_node("spot", spot_node)
    builder.add_node("work", work_node)
    builder.add_node("rework", rework_node)
    builder.add_edge(START, "spot")
    builder.add_edge("spot", "work")
    builder.add_conditional_edges("work", router_after_work, {"finish": END, "rework": "rework"})
    builder.add_edge("rework", "work")
    graph = builder.compile()
    state = graph.invoke({"request": "前端页面和测试用例"})
    print("校园 AI 社小图使用 LangGraph 流转后收工:")
    for r in state["results"]:
        print(f"  · {r.assignee}: {r.data}")


if __name__ == "__main__":
    main()
