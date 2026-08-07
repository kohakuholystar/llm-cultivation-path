"""天庭 · s4:接入 DeepSeek,Supervisor 智能分派

s3 的关键词路由是死规则,本步请 deepseek-v4-pro 当军师拆需求。
"""
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


SUPERVISOR_PROMPT = """你是天庭的玉帝,把下面的需求拆成任务单。
只输出 JSON 数组,每项含 "title" 与 "assignee";
assignee 从 [前端仙官, 后端仙官, 测试仙官, 文档仙官] 中选。需求: {request}"""


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
    #       if not tasks: tasks = [AgentTask(id="t1", title=state["request"], assignee="后端仙官")]
    #       return {"tasks": tasks}
    raise NotImplementedError("t51-supervisor-s4 尚未实现:请按 TODO 提示补齐 split_by_llm_node 拆单")


def execute_node(state: dict) -> dict:
    fmt = {"前端仙官": "已产出页面骨架: {}", "测试仙官": "已编写测试用例 {} 条,全部通过",
           "文档仙官": "文档已更新: {}", "后端仙官": "后端接口已就绪: {}"}
    return {"results": [TaskResult(task_id=t.id, assignee=t.assignee, ok=True,
                                   data=fmt[t.assignee].format(len(t.title) if t.assignee == "测试仙官" else t.title))
                        for t in state["tasks"]]}


def main() -> None:
    graph = StateGraph()
    graph.add_node("split", split_by_llm_node)
    graph.add_node("execute", execute_node)
    graph.set_entry_point("split")
    graph.add_edge("split", "execute")
    state = graph.run({"request": "开发一个登录页,后端提供登录接口,再写点测试"})
    print(f"玉帝拆出 {len(state['tasks'])} 张任务单,仙官开工:")
    for r in state["results"]:
        print(f"  · {r.assignee}: {r.data}")


if __name__ == "__main__":
    main()
