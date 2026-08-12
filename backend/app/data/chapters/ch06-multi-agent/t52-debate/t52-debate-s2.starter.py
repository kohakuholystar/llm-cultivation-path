"""校园 AI 社辩论 · s2:交锋回合与轮次编排

立场已固化,本步让两位辩论员真正交锋。把「回合」抽象成一个简单
状态机:Debate 类负责记录全部发言(transcript),并按轮次轮换取句,
让反驳不重复、先后有秩序——这是把真实 LLM 请进来之前先跑通的
纯逻辑骨架。跑完两轮,你应该得到 6 条记录:2 条立论 + 4 条交锋。
"""


# === 学习契约（面向学生）===
# 本节目标：交锋回合:交替反驳与轮次编排。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Debater`：承载本节状态/数据；重点方法：opening_statement。
#   - `Debate`：承载本节状态/数据；重点方法：opening_round, rebut, run。
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

# 反驳词库:每个立场两句,按轮次循环取用
REBUTTAL_SCRIPT = {
    "支持": ["自动化能把错误率压到接近零,人工复核反而引入主观偏差。",
             "先全自动上线再灰度观测,比事事等人拍板更快暴露问题。"],
    "反对": ["校园助手一旦误判,影响的是成千上万使用者,快不等于对。",
             "人工复核不是拖慢上线,而是给 Agent 的决策兜底。"],
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

    def opening_statement(self) -> str:
        """输出开篇立论,立场铁打不动。"""
        return f"{self.role}·{self.name} 立论:{OPENING_SCRIPT[self.stance]}"


class Debate:
    """回合制辩论编排器:记录发言并按轮次轮换取句。"""

    def __init__(self, debaters: list[Debater]) -> None:
        self.debaters = debaters
        self.transcript: list[str] = []
        self._used: dict[str, int] = {}

    def opening_round(self) -> None:
        for d in self.debaters:
            line = d.opening_statement()
            self.transcript.append(line)
            print(line)

    def rebut(self, debater: Debater) -> str:
        # TODO: 按立场取反驳词库,轮次循环取句不重复,返回一句反驳并推进指针
        # 提示: idx = self._used.get(debater.stance, 0)
        #       script = REBUTTAL_SCRIPT[debater.stance]
        #       line = script[idx % len(script)]
        #       self._used[debater.stance] = idx + 1
        #       return line
        raise NotImplementedError("t52-debate-s2 尚未实现:请按 TODO 提示补齐 rebut 反驳")

    def run(self, rounds: int = 2) -> list[str]:
        # TODO: 先立论一轮,再按轮次让两位辩论员交替反驳,记录并打印,返回完整记录
        # 提示: self.opening_round()
        #       for r in range(1, rounds + 1):
        #           for d in self.debaters:
        #               line = f"[第{r}轮] {d.role}·{d.name}:{self.rebut(d)}"
        #               self.transcript.append(line); print(line)
        #       return self.transcript
        raise NotImplementedError("t52-debate-s2 尚未实现:请按 TODO 提示补齐 run 轮次编排")


def main() -> None:
    debaters = [
        Debater("产品负责人", "正方", "支持"),
        Debater("风险审查员", "反方", "反对"),
    ]
    records = Debate(debaters).run(rounds=2)
    print(f"\n[辩论记录] 共 {len(records)} 条,交锋完成。")


if __name__ == "__main__":
    main()
