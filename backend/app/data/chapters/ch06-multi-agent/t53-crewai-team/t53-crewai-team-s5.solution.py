"""天庭 · s5:天庭总装,完整项目协作闭环

收官总装:五位神职、六道军令组成完整流水线,执行完毕把全部产出
汇总成《天庭协作纪要》落盘,体验多 Agent 项目的完整生命周期。
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
    """天庭班子:四位执行神职 + 收官文官。"""
    return [Agent("产品经理", "把用户诉求翻译成清晰需求", "凡间走一遭,最懂用户要什么。"),
            Agent("后端工程师", "把需求落成可靠接口", "内务府执笔,契约先行,数据为王。"),
            Agent("前端工程师", "把接口画成可用界面", "凌云殿画师,像素与交互皆精。"),
            Agent("测试工程师", "把风险挡在上线之前", "雷部判官,专门挑刺。"),
            Agent("收官文官", "汇总全部产出,撰写天庭协作纪要", "凌霄殿书记官。")]


@dataclass
class Task:
    """军令:干什么、验收标准、交给谁。"""

    description: str
    expected_output: str
    role: str


def build_full_plan() -> list[Task]:
    """天庭总装图:六道军令,顺序即依赖顺序。"""
    return [
        Task("需求分析:调研用户诉求,产出需求文档与功能清单",
             "一份需求文档,列出至少 3 个核心功能", "产品经理"),
        Task("API 设计:依据需求文档设计接口契约与数据模型",
             "接口设计文档,含路径、参数与响应示例", "后端工程师"),
        Task("后端实现:按接口设计文档实现服务端逻辑与数据存储",
             "可调用的后端服务,接口全部通过自测", "后端工程师"),
        Task("前端实现:按接口文档实现页面并接入真实数据",
             "可运行的界面,展示真实接口数据", "前端工程师"),
        Task("测试验收:设计用例覆盖核心功能,输出验收结论",
             "测试报告,标注通过/失败的用例清单", "测试工程师"),
        Task("收官报告:汇总各阶段产出,撰写天庭协作纪要",
             "协作纪要文档,六阶段产出一目了然", "收官文官"),
    ]


def build_llm() -> ChatOpenAI:
    """装配 DeepSeek 客户端(OpenAI 兼容协议)。"""
    return ChatOpenAI(model=MODEL, api_key=os.environ["OPENAI_API_KEY"],
                      base_url=BASE_URL, temperature=0)


# 离线剧本:五位神职照剧本演完整出戏
MOCK_OUTPUT = {
    "产品经理": "【剧本】需求文档:已梳理用户诉求,列出核心功能清单。",
    "后端工程师": "【剧本】后端服务:接口全部实现并通过自测。",
    "前端工程师": "【剧本】界面:页面完成,已接入真实接口数据。",
    "测试工程师": "【剧本】测试报告:核心用例全部通过,准予上线。",
    "收官文官": "【剧本】协作纪要:六阶段产出已汇总成文。",
}


def mock_output(role: str) -> str:
    """按角色取剧本台词。"""
    return MOCK_OUTPUT[role]


def ask_llm(llm: ChatOpenAI, agent: Agent, task: Task) -> str:
    """派活:角色卡 + 军令 + 验收标准,拼成一次对话。"""
    system = (
        f"你是{agent.role}。目标:{agent.goal}。"
        f"背景:{agent.backstory}。请始终用中文作答。"
    )
    user = f"军令:{task.description}\n验收标准:{task.expected_output}"
    return llm.invoke([SystemMessage(content=system), HumanMessage(content=user)]).content


def write_report(results: list[str]) -> str:
    """把各阶段产出汇总成天庭协作纪要,并落盘为 Markdown。"""
    lines = ["# 天庭协作纪要", "", "> 由天庭多 Agent 协作产出", ""]
    for i, output in enumerate(results, 1):
        lines.append(f"## 阶段 {i}")
        lines.append(output)
        lines.append("")
    report = "\n".join(lines)
    with open("天庭协作纪要.md", "w", encoding="utf-8") as f:
        f.write(report)
    return report


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

    def _run_one(self, agent: Agent, task: Task) -> str:
        """执行一道军令:离线走剧本,在线走真模型。"""
        if MOCK:
            return mock_output(agent.role)
        return ask_llm(build_llm(), agent, task)

    def kickoff(self) -> list[str]:
        """启动流程:逐令执行,收集各阶段产出。"""
        assert self.process == "sequential", "本步只演示顺序流程"
        results = []
        for i, task in enumerate(self.tasks, 1):
            agent = self._agent_for(task.role)
            print(f"阶段 {i}/{len(self.tasks)} · {task.role}:{task.description}")
            output = self._run_one(agent, task)
            results.append(output)
            print(f"  完成:{output[:36]}...")
        return results


def main() -> None:
    crew = Crew(agents=build_heaven(), tasks=build_full_plan(), process="sequential")
    results = crew.kickoff()
    report = write_report(results)
    print(f"\n协作纪要已落盘(天庭协作纪要.md,共 {len(report)} 字符):")
    print(report[:120] + " ...")


if __name__ == "__main__":
    main()
