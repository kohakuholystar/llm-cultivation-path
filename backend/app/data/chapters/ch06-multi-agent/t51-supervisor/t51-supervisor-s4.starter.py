"""校园 AI 社 · s4:接入 DeepSeek,Supervisor 智能分派

s3 的关键词路由是死规则,本步请 deepseek-v4-pro 当军师拆需求。
"""


# === 学习契约（面向学生）===
# 本节目标：LangGraph Supervisor：DeepSeek 智能分派。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `build_llm() -> ChatOpenAI`：输入为签名中的参数；输出为 `ChatOpenAI`。用途：按本节调用链完成对应处理
#   - `parse_tasks(content: str) -> list[AgentTask]`：输入为签名中的参数；输出为 `list[AgentTask]`。用途：按本节调用链完成对应处理
#   - `split_by_llm_node(state: dict) -> dict`：输入为签名中的参数；输出为 `dict`。用途：按本节调用链完成对应处理
#   - `execute_node(state: dict) -> dict`：输入为签名中的参数；输出为 `dict`。用途：按本节调用链完成对应处理
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `AgentTask`：承载本节状态/数据；重点方法：见类定义。
#   - `TaskResult`：承载本节状态/数据；重点方法：见类定义。
#   - `StateGraph`：承载本节状态/数据；重点方法：add_node, add_edge, set_entry_point, run。
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import json, os, sys

from dataclasses import dataclass
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

MOCK = os.environ.get("MOCK_LLM") == "1"

if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)


@dataclass
class AgentTask:
    id: str
    title: str
    assignee: str = ""


@dataclass
class TaskResult:
    task_id: str
    assignee: str
    ok: bool
    data: str = ""


END = "END"


class StateGraph:
    """最简状态图引擎:节点 + 边 + 入口,END 即收工。"""

    def __init__(self) -> None:
        self._nodes: dict[str, object] = {}
        self._edges: dict[str, str] = {}
        self._entry: str = ""

    def add_node(self, name: str, func) -> None:
        self._nodes[name] = func

    def add_edge(self, src: str, dst: str) -> None:
        self._edges[src] = dst

    def set_entry_point(self, name: str) -> None:
        self._entry = name

    def run(self, initial: dict, max_steps: int = 20) -> dict:
        state, current, steps = dict(initial), self._entry, 0
        while current != END and steps < max_steps:
            state.update(self._nodes[current](state) or {})
            current = self._edges.get(current, END)
            steps += 1
        state["_steps"] = steps
        return state


SUPERVISOR_PROMPT = """你是校园 AI 社的社长,把下面的需求拆成任务单。
只输出 JSON 数组,每项含 "title" 与 "assignee";
assignee 从 [前端同学, 后端同学, 测试同学, 文档同学] 中选。需求: {request}"""


def build_llm() -> ChatOpenAI:
    return ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
                      api_key=os.environ.get("OPENAI_API_KEY"),
                      base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                      temperature=0)


def parse_tasks(content: str) -> list[AgentTask]:
    # TODO: 剥掉 markdown 围栏,json.loads 解析后逐项转 AgentTask,失败降级返回空列表
    # 提示: text = content.strip().strip("`").strip()
    #       if text.startswith("json"): text = text[4:].strip()
    #       items = json.loads(text)
    #       return [AgentTask(id=f"t{i}", title=it["title"], assignee=it["assignee"])
    #               for i, it in enumerate(items, start=1)]
    #       except Exception: return []
    raise NotImplementedError("t51-supervisor-s4 尚未实现:请按 TODO 提示补齐 parse_tasks 解析")


def split_by_llm_node(state: dict) -> dict:
    # TODO: MOCK 走剧本三单;真实分支调模型并解析,空结果回退兜底单
    # 提示: if MOCK: return {"tasks": [剧本三单]}
    #       llm = build_llm()
    #       reply = llm.invoke([HumanMessage(content=SUPERVISOR_PROMPT.format(request=state["request"]))])
    #       tasks = parse_tasks(reply.content)
    #       if not tasks: tasks = [AgentTask(id="t1", title=state["request"], assignee="后端同学")]
    #       return {"tasks": tasks}
    raise NotImplementedError("t51-supervisor-s4 尚未实现:请按 TODO 提示补齐 split_by_llm_node 拆单")


def execute_node(state: dict) -> dict:
    fmt = {"前端同学": "已产出页面骨架: {}", "测试同学": "已编写测试用例 {} 条,全部通过",
           "文档同学": "文档已更新: {}", "后端同学": "后端接口已就绪: {}"}
    return {"results": [TaskResult(task_id=t.id, assignee=t.assignee, ok=True,
                                   data=fmt[t.assignee].format(len(t.title) if t.assignee == "测试同学" else t.title))
                        for t in state["tasks"]]}


def main() -> None:
    graph = StateGraph()
    graph.add_node("split", split_by_llm_node)
    graph.add_node("execute", execute_node)
    graph.set_entry_point("split")
    graph.add_edge("split", "execute")
    state = graph.run({"request": "开发一个登录页,后端提供登录接口,再写点测试"})
    print(f"社长拆出 {len(state['tasks'])} 张任务单,社团成员开工:")
    for r in state["results"]:
        print(f"  · {r.assignee}: {r.data}")


if __name__ == "__main__":
    main()
