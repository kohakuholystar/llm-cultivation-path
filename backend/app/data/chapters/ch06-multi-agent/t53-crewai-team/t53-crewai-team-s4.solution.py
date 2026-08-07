"""天庭 · s4:层级流程,总管分派,层层上报

角色卡与作战图就位,本步点亮指挥链:新增「天庭总管」逐令签发分派令,
执行者按令干活并上报,复刻 CrewAI 的 hierarchical process。
"""
import os
import sys

from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-pro"
MOCK = os.environ.get("MOCK_LLM") == "1"  # 离线演示模式

if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[天庭] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    print("(本地离线演示可设 MOCK_LLM=1,用剧本模拟模型决策)")
    sys.exit(0)


@dataclass
class Agent:
    """角色卡:role 你是谁,goal 要达成什么,backstory 立场与专长。"""

    role: str
    goal: str
    backstory: str


def build_heaven() -> list[Agent]:
    """天庭班子:四位执行神职。"""
    return [Agent("产品经理", "把用户诉求翻译成清晰需求", "凡间走一遭,最懂用户要什么。"),
            Agent("后端工程师", "把需求落成可靠接口", "内务府执笔,契约先行,数据为王。"),
            Agent("前端工程师", "把接口画成可用界面", "凌云殿画师,像素与交互皆精。"),
            Agent("测试工程师", "把风险挡在上线之前", "雷部判官,专门挑刺。")]


# 层级流程的灵魂:一位总览全局、分派任务、验收结果的总管
MANAGER = Agent(
    role="天庭总管",
    goal="统筹全局,把任务分派给最合适的神职并验收结果",
    backstory="天庭最高指挥官,握有所有成员的职能档案。",
)


@dataclass
class Task:
    """军令:干什么、验收标准、交给谁。"""

    description: str
    expected_output: str
    role: str


def build_plan() -> list[Task]:
    """天庭作战图:四道军令,顺序即依赖顺序。"""
    return [
        Task("需求分析:调研用户诉求,产出需求文档与功能清单", "一份需求文档,列出至少 3 个核心功能", "产品经理"),
        Task("API 设计:依据需求文档设计接口契约与数据模型", "接口设计文档,含路径、参数与响应示例", "后端工程师"),
        Task("前端开发:按接口文档实现页面并与 API 联调", "可运行的界面,展示真实接口数据", "前端工程师"),
        Task("测试验收:设计用例覆盖核心功能,输出验收结论", "测试报告,标注通过/失败的用例清单", "测试工程师"),
    ]


def build_llm() -> ChatOpenAI:
    """装配 DeepSeek 客户端(OpenAI 兼容协议)。"""
    return ChatOpenAI(model=MODEL, api_key=os.environ["OPENAI_API_KEY"],
                      base_url=BASE_URL, temperature=0)


# 离线剧本:总管与四位神职照剧本演完整出戏
MOCK_OUTPUT = {
    "天庭总管": "【剧本】分派令:此令交由对应神职执行,按验收标准完成后上报。",
    "产品经理": "【剧本】需求文档:已梳理用户诉求,列出核心功能清单。",
    "后端工程师": "【剧本】接口设计文档:路径、参数与响应示例已就绪。",
    "前端工程师": "【剧本】界面:页面完成,已与 API 联调展示真实数据。",
    "测试工程师": "【剧本】测试报告:核心用例全部通过,准予上线。",
}


def mock_output(role: str) -> str:
    """按角色取剧本台词。"""
    return MOCK_OUTPUT[role]


def ask_llm(llm: ChatOpenAI, agent: Agent, task: Task, extra: str = "") -> str:
    """派活:角色卡 + 军令 + 验收标准 + 参考材料,拼成一次对话。"""
    system = f"你是{agent.role}。目标:{agent.goal}。背景:{agent.backstory}。请始终用中文作答。"
    user = f"军令:{task.description}\n验收标准:{task.expected_output}"
    if extra: user += f"\n参考材料:{extra}"
    return llm.invoke([SystemMessage(content=system), HumanMessage(content=user)]).content


class Crew:
    """天庭施工队:按流程设定,把军令依次派给合适的神职。"""

    def __init__(self, agents: list[Agent], tasks: list[Task],
                 process: str = "sequential", manager=None) -> None:
        self.agents = agents
        self.tasks = tasks
        self.process = process
        self.manager = manager

    def _agent_for(self, role: str) -> Agent:
        """按角色名找到执行者。"""
        return next(a for a in self.agents if a.role == role)

    def _plan_order(self, llm: ChatOpenAI | None, task: Task) -> str:
        """签发分派令:无总管走例行分派,离线走剧本,在线问总管。"""
        if self.manager is None:
            return f"例行分派:此令交由 {task.role} 执行,按验收标准完成。"
        if MOCK:
            return mock_output("天庭总管")
        return ask_llm(llm, self.manager, task, "")

    def _run_one(self, agent: Agent, task: Task, extra: str) -> str:
        """执行一道军令:离线走剧本,在线走真模型。"""
        if MOCK:
            return mock_output(agent.role)
        return ask_llm(build_llm(), agent, task, extra)

    def kickoff(self) -> list[str]:
        """启动指挥链:总管逐令签令,执行者按令干活并上报。"""
        assert self.process == "hierarchical", "本步只演示层级流程"
        results = []
        llm = None if MOCK else build_llm()
        prev = ""
        for i, task in enumerate(self.tasks, 1):
            order = self._plan_order(llm, task)
            print(f"军令 {i}/{len(self.tasks)} · 分派令:{order[:36]}...")
            agent = self._agent_for(task.role)
            output = self._run_one(agent, task, prev)
            results.append(output)
            prev = output
            print(f"  执行者 {agent.role} 完成,结果已上报总管:{output[:36]}...")
        return results


def main() -> None:
    crew = Crew(agents=build_heaven(), tasks=build_plan(),
                process="hierarchical", manager=MANAGER)
    results = crew.kickoff()
    print(f"\n指挥链执行完毕,共收到 {len(results)} 份上报结果。")


if __name__ == "__main__":
    main()
