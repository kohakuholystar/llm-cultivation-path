"""天庭 · s3:分派、执行与返工

把迷你状态图拼成 Supervisor 编排骨架:拆需求 -> 派活 -> 执行 -> 检查,
用 FAIL_ONCE 模拟偶发故障,t2 首跑失败后经返工回路收敛。
"""
from dataclasses import dataclass


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


END = "END"


# 模拟偶发故障:t2 首跑必败,返工后恢复正常
FAIL_ONCE = {"t2"}


class StateGraph:
    """极简状态图引擎(s2 复刻):节点函数 + 边 + 条件边。"""

    def __init__(self) -> None:
        self._nodes: dict[str, object] = {}
        self._edges: dict[str, str] = {}
        self._conditional: dict[str, tuple] = {}
        self._entry: str = ""

    def add_node(self, name: str, func) -> None:
        self._nodes[name] = func

    def add_edge(self, src: str, dst: str) -> None:
        self._edges[src] = dst

    def add_conditional_edges(self, src: str, router, mapping: dict) -> None:
        self._conditional[src] = (router, mapping)

    def set_entry_point(self, name: str) -> None:
        self._entry = name

    def run(self, initial: dict, max_steps: int = 20) -> dict:
        state = dict(initial)
        current = self._entry
        steps = 0
        while current != END and steps < max_steps:
            out = self._nodes[current](state)
            if out:
                state.update(out)
            if current in self._conditional:
                router, mapping = self._conditional[current]
                current = mapping.get(router(state), END)
            else:
                current = self._edges.get(current, END)
            steps += 1
        state["_steps"] = steps
        return state


def split_node(state: dict) -> dict:
    tasks = [AgentTask(id=f"t{i}", title=t, assignee="后端仙官")
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
    graph = StateGraph()
    graph.add_node("split", split_node)
    graph.add_node("execute", execute_node)
    graph.add_node("retry", retry_node)
    graph.set_entry_point("split")
    graph.add_edge("split", "execute")
    graph.add_conditional_edges("execute", router_after_execute, {"retry": "retry", "END": END})
    graph.add_edge("retry", "execute")
    state = graph.run({"request": "前端页面设计和后端接口联调"})
    print(f"天庭流转 {state['_steps']} 步{'(含返工)' if state.get('retried') else ''},共 {len(state['tasks'])} 张任务单:")
    for r in state["results"]:
        print(f"  · {r.assignee}: {r.data}")
    print("全部完工,可交付。")


if __name__ == "__main__":
    main()
