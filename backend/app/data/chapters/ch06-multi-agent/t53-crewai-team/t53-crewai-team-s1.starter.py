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
    # TODO: 定义四个字段:role / goal / backstory 为 str,tools 用 field 提供空列表默认值
    # 提示: 无默认值字段在前;tools: list[str] = field(default_factory=list)
    pass


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
    # TODO: 返回 4 个带中文设定与工具的 Agent
    # 提示: Agent(role=..., goal=..., backstory=..., tools=[...])
    raise NotImplementedError("build_heaven 尚未实现:请按 TODO 提示返回 4 个 Agent(...) 组成的列表")


def main() -> None:
    print("== 天庭神职名册 ==")
    for agent in build_heaven():
        print(role_card(agent))
        print("-" * 40)


if __name__ == "__main__":
    main()
