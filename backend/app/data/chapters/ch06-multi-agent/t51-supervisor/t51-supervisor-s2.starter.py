"""校园 AI 社 · s2:手写迷你 StateGraph,节点与边

上一张任务单已经能分派,本步动手写一个 60 行的迷你状态图引擎:
节点是普通函数,边决定流转方向;条件边由 router 函数看状态选路。
最后用一张校园 AI 社小图把「拆需求 -> 派活 -> 汇报」串起来跑通。
"""


# === 学习契约（面向学生）===
# 本节目标：LangGraph：节点、边与条件路由。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `spot_node(state: dict) -> dict`：输入为签名中的参数；输出为 `dict`。用途：任务分派:把需求文档按「和」拆成任务单,分派给对应社团成员。
#   - `work_node(state: dict) -> dict`：输入为签名中的参数；输出为 `dict`。用途：开工:每张任务单产出完工汇报。
#   - `router_after_work(state: dict) -> str`：输入为签名中的参数；输出为 `str`。用途：完工检查:有汇报就去汇报,没有就返工。
#   - `rework_node(state: dict) -> dict`：输入为签名中的参数；输出为 `dict`。用途：兜底返工:补一张通用任务单,重新开工。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `AgentTask`：承载本节状态/数据；重点方法：见类定义。
#   - `TaskResult`：承载本节状态/数据；重点方法：见类定义。
#   - `StateGraph`：承载本节状态/数据；重点方法：add_node, add_edge, add_conditional_edges, set_entry_point, run。
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
from dataclasses import dataclass


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


END = "END"  # 终点哨兵:流转到它,执行循环就停


class StateGraph:
    """极简状态图:节点函数 + 普通边 + 条件边 + 入口。"""

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
        # TODO: 把 (router, mapping) 存进条件边表,供 run 按状态选路
        # 提示: self._conditional[src] = (router, mapping)
        raise NotImplementedError("t51-supervisor-s2 尚未实现:请按 TODO 提示补齐 add_conditional_edges")

    def set_entry_point(self, name: str) -> None:
        self._entry = name

    def run(self, initial: dict, max_steps: int = 20) -> dict:
        """从入口节点循环执行,直到 END 或步数用尽。"""
        state = dict(initial)
        current = self._entry
        steps = 0
        # TODO: 循环调节点直到 END 或步数用尽,普通边/条件边走不同选路
        # 提示: while current != END and steps < max_steps:
        #           out = self._nodes[current](state)
        #           if out: state.update(out)
        #           if current in self._conditional:
        #               router, mapping = self._conditional[current]
        #               current = mapping.get(router(state), END)
        #           else:
        #               current = self._edges.get(current, END)
        #           steps += 1
        state["_steps"] = steps
        return state


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
    graph = StateGraph()
    graph.add_node("spot", spot_node)
    graph.add_node("work", work_node)
    graph.add_node("rework", rework_node)
    graph.set_entry_point("spot")
    graph.add_edge("spot", "work")
    graph.add_conditional_edges("work", router_after_work, {"finish": END, "rework": "rework"})
    graph.add_edge("rework", "work")
    state = graph.run({"request": "前端页面和测试用例"})
    print(f"校园 AI 社小图流转 {state['_steps']} 步后收工:")
    for r in state["results"]:
        print(f"  · {r.assignee}: {r.data}")


if __name__ == "__main__":
    main()
