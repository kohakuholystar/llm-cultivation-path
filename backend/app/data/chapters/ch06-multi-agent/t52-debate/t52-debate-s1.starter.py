"""校园 AI 社辩论 · s1:立场固化与开篇立论

校园 AI 社辩论是社团成员们用 Agent 模拟的多角色辩论流水线,第一个环节是
「立场固化」:用模板字符串为每位辩论员生成专属系统提示词,把身份、
辩题与立场牢牢写进系统层,再输出开篇立论。

立场是辩论的根:一旦固化,后续所有发言都不得偏离——这是回合制
交锋的前提,也是多 Agent 辩论与自由对话最本质的区别。本步只讲
「立得住」,交锋与裁决留给后面的步骤。先立人设,再论输赢。
"""


# === 学习契约（面向学生）===
# 本节目标：辩论员诞生:立场固化与开篇立论。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Debater`：承载本节状态/数据；重点方法：describe, opening_statement。
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
        # TODO: 用模板生成系统提示词,把身份、辩题与立场写进系统层
        # 提示: self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        #           role=role, name=name, topic=DEBATE_TOPIC, stance=stance,
        #       )
        raise NotImplementedError("t52-debate-s1 尚未实现:请按 TODO 提示补齐系统提示词生成")

    def describe(self) -> str:
        """一句话自我介绍,用于对阵展示。"""
        return f"{self.role}·{self.name}(立场:{self.stance})"

    def opening_statement(self) -> str:
        """输出开篇立论,立场铁打不动。"""
        # TODO: 从剧本查立场对应的立论,返回带身份的格式化文本
        # 提示: return f"{self.role}·{self.name} 立论:{OPENING_SCRIPT[self.stance]}",不要 print
        raise NotImplementedError("t52-debate-s1 尚未实现:请按 TODO 提示补齐 opening_statement 立论")


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
