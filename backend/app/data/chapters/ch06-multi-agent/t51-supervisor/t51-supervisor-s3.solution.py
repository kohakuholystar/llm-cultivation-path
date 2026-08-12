"""校园 AI 社 · s3:分派、执行与返工

把迷你状态图拼成 Supervisor 编排骨架:拆需求 -> 派活 -> 执行 -> 检查,
用 FAIL_ONCE 模拟偶发故障,t2 首跑失败后经返工回路收敛。
"""
from dataclasses import dataclass
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


@dataclass
class AgentTask:
    id: str
    title: str
    assignee: str = ""
    payload: str = ""


@dataclass
class TaskResult:
    task_id: str
    assignee: str
    ok: bool
    data: str = ""
    error: str = ""


# 模拟偶发故障:t2 首跑必败,返工后恢复正常
FAIL_ONCE = {"t2"}


class WorkflowState(TypedDict, total=False):
    request: str
    tasks: list[AgentTask]
    results: list[TaskResult]
    retried: bool


def split_node(state: dict) -> dict:
    tasks = [AgentTask(id=f"t{i}", title=t, assignee="后端同学")
             for i, t in enumerate(state["request"].split("和"), start=1)]
    return {"tasks": tasks}


def execute_node(state: dict) -> dict:
    results = []
    for t in state["tasks"]:
        if t.id in FAIL_ONCE:
            results.append(TaskResult(task_id=t.id, assignee=t.assignee, ok=False,
                                      error="偶发故障:服务超时"))
        else:
            results.append(TaskResult(task_id=t.id, assignee=t.assignee, ok=True,
                                      data=f"后端接口已就绪: {t.title}"))
    return {"results": results}


def router_after_execute(state: dict) -> str:
    return "retry" if any(not r.ok for r in state["results"]) else "END"


def retry_node(state: dict) -> dict:
    FAIL_ONCE.clear()  # 故障已排除,下一轮执行恢复正常
    return {"retried": True}


def main() -> None:
    builder = StateGraph(WorkflowState)
    builder.add_node("split", split_node)
    builder.add_node("execute", execute_node)
    builder.add_node("retry", retry_node)
    builder.add_edge(START, "split")
    builder.add_edge("split", "execute")
    builder.add_conditional_edges("execute", router_after_execute, {"retry": "retry", "END": END})
    builder.add_edge("retry", "execute")
    graph = builder.compile()
    state = graph.invoke({"request": "前端页面设计和后端接口联调"}, {"recursion_limit": 10})
    print(f"校园 AI 社使用 LangGraph{'(含返工)' if state.get('retried') else ''},共 {len(state['tasks'])} 张任务单:")
    for r in state["results"]:
        print(f"  · {r.assignee}: {r.data}")
    print("全部完工,可交付。")


if __name__ == "__main__":
    main()
