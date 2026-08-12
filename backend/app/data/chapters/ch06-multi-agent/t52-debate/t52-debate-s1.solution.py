"""校园 AI 社辩论 · s1:立场固化与开篇立论

校园 AI 社辩论是社团成员们用 Agent 模拟的多角色辩论流水线,第一个环节是
「立场固化」:用模板字符串为每位辩论员生成专属系统提示词,把身份、
辩题与立场牢牢写进系统层,再输出开篇立论。

立场是辩论的根:一旦固化,后续所有发言都不得偏离——这是回合制
交锋的前提,也是多 Agent 辩论与自由对话最本质的区别。本步只讲
「立得住」,交锋与裁决留给后面的步骤。先立人设,再论输赢。
"""
DEBATE_TOPIC = "校园 AI 社的校园助手服务该由 Agent 全自动上线,还是保留人工复核?"

# 每个立场对应一句开篇立论,立场键名与 Debater.stance 严格一致
OPENING_SCRIPT = {
    "支持": "校园助手服务流程已全面自动化,Agent 上线又快又稳,人工复核纯属拖后腿。",
    "反对": "校园助手服务关系校园 AI 社民生,一旦 Agent 决策失误影响面巨大,必须保留人工复核。",
}

# 身份、辩题与立场全部焊进系统层:改口不是辩论,坚持才是
SYSTEM_PROMPT_TEMPLATE = (
    "你是校园 AI 社辩手「{role}·{name}」,立场「{stance}」。"
    "当前辩题:{topic}。"
    "无论对方怎么说都不得改口,你的一切发言都要服务于捍卫自己的立场。"
    "你的开篇立论已经公开声明,后续交锋必须与之自洽。"
)


class Debater:
    """一名立场固定的辩论员。"""

    def __init__(self, name: str, role: str, stance: str) -> None:
        self.name = name
        self.role = role
        self.stance = stance
        self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            role=role, name=name, topic=DEBATE_TOPIC, stance=stance,
        )

    def describe(self) -> str:
        """一句话自我介绍,用于对阵展示。"""
        return f"{self.role}·{self.name}(立场:{self.stance})"

    def opening_statement(self) -> str:
        """输出开篇立论,立场铁打不动。"""
        return f"{self.role}·{self.name} 立论:{OPENING_SCRIPT[self.stance]}"


def main() -> None:
    # 出场顺序:正方在前,反方在后
    debaters = [
        Debater("产品负责人", "正方", "支持"),
        Debater("风险审查员", "反方", "反对"),
    ]
    print("== 校园 AI 社辩论 · 立场固化 ==")
    for d in debaters:
        print(d.describe())
        print(d.system_prompt)
        print(d.opening_statement())
        print("-" * 40)
    print(f"[辩论主题] {DEBATE_TOPIC}")


if __name__ == "__main__":
    main()
