"""Agent 运行时底座 · s6:总装——黑盒上下文管理器

前五步的散件(称重、滚动摘要、重要性评分、淘汰、溢出恢复)
在本步拧成一根完整的轴:外部只调用 add / snapshot / stats
三个动作,内部自动称重、自动折叠、自动淘汰,窗口永不溢出。"""

from dataclasses import dataclass
import math
import re


CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def heuristic_tokens(text: str) -> int:
    cjk = len(CJK_RE.findall(text))
    rest = re.sub(r"\s", "", CJK_RE.sub("", text))
    return max(cjk + math.ceil(len(rest) / 4), 1)


@dataclass
class Message:
    """一条带权重的对话消息。"""
    role: str
    content: str
    tokens: int = 0

    def __post_init__(self):
        if self.tokens <= 0:
            self.tokens = heuristic_tokens(self.content)


@dataclass
class TokenBudget:
    """上下文预算:总容量与输出预留。"""
    total: int = 900
    reserve_output: int = 760

    @property
    def max_context(self) -> int:
        return self.total - self.reserve_output

    def used(self, messages: list) -> int:
        return sum(m.tokens for m in messages)

    def fits(self, messages: list) -> bool:
        return self.used(messages) <= self.max_context


def make_summary(messages: list, max_chars: int = 100) -> str:
    pairs = [f"{m.role}:{m.content}" for m in messages]
    text = "；".join(pairs)
    return text[:max_chars]


class SummaryBuffer:
    def __init__(self, max_chars: int = 100):
        self.max_chars = max_chars
        self.text = ""

    def fold(self, messages: list) -> int:
        combined = [Message("system", self.text)] if self.text else []
        self.text = make_summary(combined + messages, self.max_chars)
        return len(combined + messages)


def importance_score(m: Message, index: int, total: int) -> float:
    base = 0.0 if m.role == "system" else 10.0
    return base + 20.0 * index / max(total, 1) + min(m.tokens * 0.5, 30.0)


def evict_lowest(messages: list, budget: TokenBudget, actions: list) -> int:
    evicted = 0
    while not budget.fits(messages):
        candidates = [m for m in messages[1:] if m.role != "system"]
        if not candidates:
            break
        scored = sorted(
            ((importance_score(m, i, len(candidates)), m)
             for i, m in enumerate(candidates)),
            key=lambda p: p[0],
        )
        victim = scored[0][1]
        messages.remove(victim)
        evicted += 1
        actions.append(f"淘汰低价值消息 {victim.content[:8]}")
    return evicted


def recover_overflow(current: list, budget: TokenBudget, summary: SummaryBuffer) -> tuple:
    actions = []
    folded = 0
    if not budget.fits(current) and len(current) > 2:
        old = current[1:-4] if len(current) > 5 else []
        if old:
            folded = summary.fold(old)
            for m in old:
                current.remove(m)
            current.insert(1, Message("system", summary.text))
            actions.append(f"摘要折叠 {folded} 条")
    evict_lowest(current, budget, actions)
    if not budget.fits(current):
        raise ValueError("窗口仍然溢出")
    return current, actions, folded


class ContextManager:
    """Agent 运行时底座总装:对外只暴露 add / snapshot / stats 三个动作。"""

    def __init__(self, budget=None, summary_max_chars: int = 200):
        self.budget = budget or TokenBudget(total=900, reserve_output=760)
        self.summary = SummaryBuffer(max_chars=summary_max_chars)
        self.messages: list[Message] = []
        self.folded = 0
        self.evicted = 0

    def snapshot(self) -> list:
        """返回消息列表的防御性副本,外部修改不影响内部状态。"""
        return list(self.messages)

    def add(self, message: Message):
        self.messages.append(message)
        if not self.budget.fits(self.snapshot()):
            current, actions, folded = recover_overflow(
                self.snapshot(), self.budget, self.summary
            )
            self.folded += folded
            self.evicted += len([a for a in actions if a.startswith("淘汰")])
            self.messages = current
            for a in actions:
                print(f"    [恢复] {a}")

    def stats(self) -> str:
        return (f"统计: 折叠 {self.folded} 条,淘汰 {self.evicted} 条,"
                f"当前用量 {self.budget.used(self.snapshot())} / {self.budget.max_context} token")


def main():
    cm = ContextManager()
    msgs = [
        Message("system", "你是Agent 运行时底座,负责管理对话窗口。"),
        Message("user", "第1轮:请汇报今日运行资源收支情况。附上月对比与结余明细。"),
        Message("assistant", "收入五千二,支出三千一,结余两千一。对比上月整体健康,无异常波动。"),
        Message("tool", "tool_result: 网络图已生成,存于黑糖资料室第三层。附各模块产量明细。"),
        Message("user", "第2轮:结余如何处置?"),
        Message("assistant", "建议三条:一扩丹房,二修大阵,三储备预算点。"),
        Message("user", "第3轮:扩丹房需多少预算点?请估算回本周期,并对比现有丹房产量与矿石品质,给出灵矿储备明细。"),
    ]
    for m in msgs:
        cm.add(m)
        print(f"加入[{m.role}]后:消息 {len(cm.snapshot())} 条(含摘要),用量 {cm.budget.used(cm.snapshot())} / {cm.budget.max_context} token")
    print(cm.stats())


if __name__ == "__main__":
    main()
