"""校园 AI 社 · s5:结果聚合与校园 AI 社总装

s4 的智能分派已经能开工,本步在末端加聚合节点:统计成败、组装交付报告,
写回共享状态,总装成完整流水线。
"""
import json, os, sys

from dataclasses import dataclass
from typing import TypedDict
from langgraph.graph import END, START, StateGraph
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


class WorkflowState(TypedDict, total=False):
    request: str
    tasks: list[AgentTask]
    results: list[TaskResult]
    report: str


SUPERVISOR_PROMPT = """你是校园 AI 社的社长,把下面的需求拆成任务单。
只输出 JSON 数组,每项含 "title" 与 "assignee";
assignee 从 [前端同学, 后端同学, 测试同学, 文档同学] 中选。需求: {request}"""


def build_llm() -> ChatOpenAI:
    return ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
                      api_key=os.environ.get("OPENAI_API_KEY"),
                      base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
                      temperature=0)


def parse_tasks(content: str) -> list[AgentTask]:
    text = content.strip().strip("`").strip()
    if text.startswith("json"):
        text = text[4:].strip()
    try:
        items = json.loads(text)
        return [AgentTask(id=f"t{i}", title=it["title"], assignee=it["assignee"])
                for i, it in enumerate(items, start=1)]
    except Exception:
        return []


def split_by_llm_node(state: dict) -> dict:
    if MOCK:
        print("[MOCK] 社长使用剧本拆解任务")
        return {"tasks": [AgentTask(id=f"t{i}", title=t, assignee=a) for i, (t, a) in
                          enumerate([("前端页面设计", "前端同学"), ("后端接口联调", "后端同学"),
                                     ("测试用例编写", "测试同学")], start=1)]}
    llm = build_llm()
    reply = llm.invoke([HumanMessage(content=SUPERVISOR_PROMPT.format(request=state["request"]))])
    tasks = parse_tasks(reply.content)
    if not tasks:
        print("[校园 AI 社] 模型输出无法解析,回退单条兜底任务")
        tasks = [AgentTask(id="t1", title=state["request"], assignee="后端同学")]
    return {"tasks": tasks}


def execute_node(state: dict) -> dict:
    fmt = {"前端同学": "已产出页面骨架: {}", "测试同学": "已编写测试用例 {} 条,全部通过",
           "文档同学": "文档已更新: {}", "后端同学": "后端接口已就绪: {}"}
    return {"results": [TaskResult(task_id=t.id, assignee=t.assignee, ok=True,
                                   data=fmt[t.assignee].format(len(t.title) if t.assignee == "测试同学" else t.title))
                        for t in state["tasks"]]}


def aggregate_node(state: dict) -> dict:
    """聚合:统计成败并组装交付报告,写回共享状态。"""
    results = state["results"]
    body = "\n".join(f"  · {r.assignee}: {r.data}" for r in results)
    report = f"校园 AI 社交付报告(成功 {sum(1 for r in results if r.ok)}/{len(results)}):\n{body}"
    return {"report": report}


def main() -> None:
    builder = StateGraph(WorkflowState)
    builder.add_node("split", split_by_llm_node)
    builder.add_node("execute", execute_node)
    builder.add_node("aggregate", aggregate_node)
    builder.add_edge(START, "split")
    builder.add_edge("split", "execute")
    builder.add_edge("execute", "aggregate")
    builder.add_edge("aggregate", END)
    state = builder.compile().invoke({"request": "开发一个登录页,后端提供登录接口,再写点测试"})
    print(state['report'])


if __name__ == "__main__":
    main()
