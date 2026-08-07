"""天庭 · s1:分神化形,Agent 角色卡入册

天庭是虚拟开发团队:产品经理、后端工程师、前端工程师、测试工程师。
本步为每位神职登记一张角色卡(role / goal / backstory / tools),
角色卡的三要素最终会拼进模型的 system prompt,决定它怎么演这个角色。
本步用纯 Python 复刻 CrewAI 的 Agent 数据结构,不依赖任何第三方库。
"""

from dataclasses import dataclass, field


@dataclass
class Agent:
    """角色卡:role 你是谁,goal 要达成什么,backstory 立场与专长。"""

    role: str
    goal: str
    backstory: str
    tools: list[str] = field(default_factory=list)


def role_card(agent: Agent) -> str:
    """把角色卡渲染成给模型看的自我介绍文本。"""
    tools = "、".join(agent.tools) if agent.tools else "无"
    return (
        f"◆ 角色:{agent.role}\n"
        f"  目标:{agent.goal}\n"
        f"  背景:{agent.backstory}\n"
        f"  工具:{tools}"
    )


def build_heaven() -> list[Agent]:
    """天庭班子:四位执行神职,各配趁手法宝。"""
    return [
        # 产品经理:负责把用户诉求翻译成需求
        Agent(
            role="产品经理",
            goal="把用户诉求翻译成清晰需求",
            backstory="凡间走一遭,最懂用户要什么。",
            tools=["需求文档"],
        ),
        # 后端工程师:负责把需求落成可靠接口
        Agent(
            role="后端工程师",
            goal="把需求落成可靠接口",
            backstory="内务府执笔,契约先行,数据为王。",
            tools=["Python", "数据库"],
        ),
        # 前端工程师:负责把接口画成可用界面
        Agent(
            role="前端工程师",
            goal="把接口画成可用界面",
            backstory="凌云殿画师,像素与交互皆精。",
            tools=["TypeScript", "React"],
        ),
        # 测试工程师:负责把风险挡在上线之前
        Agent(
            role="测试工程师",
            goal="把风险挡在上线之前",
            backstory="雷部判官,专门挑刺。",
            tools=["pytest"],
        ),
    ]


def main() -> None:
    print("== 天庭神职名册 ==")
    for agent in build_heaven():
        print(role_card(agent))
        print("-" * 40)


if __name__ == "__main__":
    main()
