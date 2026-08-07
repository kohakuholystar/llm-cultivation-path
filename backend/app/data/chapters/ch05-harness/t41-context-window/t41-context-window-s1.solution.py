"""乾坤圈 · s1:预算先行——给每条消息称重

Agent 的上下文窗口不是无限的,消息装多了就会溢出、截断甚至报错。
本步为「乾坤圈」打地基:用启发式算法估算每条消息的 token 占用,
再把预算、输出预留与可用窗口之间的账目算清楚。"""
import math
import re
from dataclasses import dataclass, field


CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def heuristic_tokens(text: str) -> int:
    """启发式估算 token 数:CJK 每字 1 token,ASCII 每 4 字符 1 token。"""
    cjk = len(CJK_RE.findall(text))
    rest = re.sub(r"\s", "", CJK_RE.sub("", text))
    return max(cjk + math.ceil(len(rest) / 4), 1)


@dataclass
class Message:
    """一条对话消息,创建时自动完成 token 称重。"""

    role: str
    content: str
    tokens: int = field(init=False, default=0)

    def __post_init__(self):
        self.tokens = heuristic_tokens(self.content)


class TokenBudget:
    """上下文预算:总预算、输出预留与可用上下文窗口。"""

    def __init__(self, total: int, reserve_output: int):
        self.total = total
        self.reserve_output = reserve_output
        self.max_context = total - reserve_output

    def used(self, messages) -> int:
        return sum(m.tokens for m in messages)

    def remaining(self, messages) -> int:
        return self.max_context - self.used(messages)

    def fits(self, messages) -> bool:
        return self.used(messages) <= self.max_context


def print_ledger(budget: TokenBudget, messages) -> None:
    """打印上下文账目:总预算、窗口、逐条占用与剩余空间。"""
    print(f"总预算 {budget.total} token,输出预留 {budget.reserve_output}")
    print(f"上下文窗口 {budget.max_context} token")
    for m in messages:
        print(f"  [{m.role}] {m.tokens:>4} token: {m.content[:18]}")
    used = budget.used(messages)
    print(f"已占用 {used} / {budget.max_context} token,剩余 {budget.remaining(messages)}")
    print(f"预算是否放得下当前消息: {budget.fits(messages)}")


def main() -> None:
    budget = TokenBudget(total=8000, reserve_output=2000)
    history = [
        Message("system", "你是乾坤圈的守门人,负责守护一座仙山的运转。"),
        Message("user", "请汇报仙山今日的灵气收支情况,并给出三条建议。"),
        Message("assistant", "遵命。今日灵气收入 5200,支出 3100,结余 2100。"),
        Message("user", "结余部分建议怎么处理?请说得详细一些。"),
        Message("assistant", "建议:一扩充炼丹房,二修缮护山大阵,三储备过冬灵石。"),
    ]
    print_ledger(budget, history)


if __name__ == "__main__":
    main()
