"""天庭 · s3:顺序流程,一令既出,依次执行

角色卡与作战图就位,本步点亮引擎:用 ChatOpenAI 接上 DeepSeek,
按顺序流程逐道执行军令,上一道的产出自动成为下一道的上下文。
"""
import os
import sys

from dataclasses import dataclass, field

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
        Task("需求分析:调研用户诉求,产出需求文档与功能清单", "一份需求文档,列出至少 3 个核心功能", "产品经理"),
        Task("API 设计:依据需求文档设计接口契约与数据模型", "接口设计文档,含路径、参数与响应示例", "后端工程师", context=["需求文档"]),
        Task("前端开发:按接口文档实现页面并与 API 联调", "可运行的界面,展示真实接口数据", "前端工程师", context=["接口设计文档"]),
        Task("测试验收:设计用例覆盖核心功能,输出验收结论", "测试报告,标注通过/失败的用例清单", "测试工程师", context=["需求文档", "界面"]),
    ]


def build_llm() -> ChatOpenAI:
    """装配 DeepSeek 客户端(OpenAI 兼容协议)。"""
    return ChatOpenAI(
        model=MODEL,
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=BASE_URL,
        temperature=0,
    )


# 离线剧本:没有 API Key 时,四位神职照剧本演完整出戏
MOCK_OUTPUT = {
    "产品经理": "【剧本】需求文档:已梳理用户诉求,列出核心功能清单。",
    "后端工程师": "【剧本】接口设计文档:路径、参数与响应示例已就绪。",
    "前端工程师": "【剧本】界面:页面完成,已与 API 联调展示真实数据。",
    "测试工程师": "【剧本】测试报告:核心用例全部通过,准予上线。",
}


def mock_output(task: Task) -> str:
    """按执行者角色取剧本台词。"""
    return MOCK_OUTPUT[task.role]


def ask_llm(llm: ChatOpenAI, agent: Agent, task: Task, context: str) -> str:
    """派活:角色卡 + 军令 + 验收标准 + 前置产出,拼成一次对话。"""
    system = (
        f"你是{agent.role}。目标:{agent.goal}。"
        f"背景:{agent.backstory}。请始终用中文作答。"
    )
    user = f"军令:{task.description}\n验收标准:{task.expected_output}"
    if context:
        user += f"\n前置产出(供参考):{context}"
    reply = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    return reply.content


class Crew:
    """天庭施工队:按流程设定,把军令依次派给合适的神职。"""

    def __init__(self, agents: list[Agent], tasks: list[Task],
                 process: str = "sequential") -> None:
        self.agents = agents
        self.tasks = tasks
        self.process = process

    def _agent_for(self, role: str) -> Agent:
        """按角色名找到执行者。"""
        return next(a for a in self.agents if a.role == role)

    def _run_one(self, agent: Agent, task: Task, context: str) -> str:
        """执行一道军令:离线走剧本,在线走真模型。"""
        if MOCK:
            return mock_output(task)
        return ask_llm(build_llm(), agent, task, context)

    def kickoff(self) -> list[str]:
        """启动流程:逐令执行,上一道产出成为下一道的上下文。"""
        assert self.process == "sequential", "本步只演示顺序流程"
        results = []
        context = ""
        for i, task in enumerate(self.tasks, 1):
            agent = self._agent_for(task.role)
            print(f"军令 {i}/{len(self.tasks)} → {task.role}:{task.description}")
            output = self._run_one(agent, task, context)
            results.append(output)
            context = output
            print(f"  产出:{output[:40]}...")
        return results


def main() -> None:
    crew = Crew(agents=build_heaven(), tasks=build_plan(), process="sequential")
    results = crew.kickoff()
    print(f"\n流水线执行完毕,共收到 {len(results)} 份产出。")


if __name__ == "__main__":
    main()
