"""Agent 运行时底座 · s5:溢出恢复——三级处置逐级收紧

窗口再精打细算也有装不下的时候:要么新消息进不来,要么旧消息被硬挤掉。
本步实现 recover_overflow:先折叠旧对话为摘要,再淘汰低价值消息,
最后整窗截断兜底,逐级收紧直到装进窗口。"""
import math
import re
from dataclasses import dataclass


CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def heuristic_tokens(text: str) -> int:
    """启发式估算 token 数:CJK 每字 1 token,ASCII 每 4 字符 1 token。"""
    cjk = len(CJK_RE.findall(text))
    rest = re.sub(r"\s", "", CJK_RE.sub("", text))
    return max(cjk + math.ceil(len(rest) / 4), 1)


@dataclass
class Message:
    """一条对话消息:角色 + 内容,token 数惰性估算。"""
    role: str
    content: str

    @property
    def tokens(self) -> int:
        return heuristic_tokens(self.content)


@dataclass
class TokenBudget:
    """窗口预算:总量 - 输出预留 = 可用上下文。"""
    total: int = 900
    reserve_output: int = 760

    @property
    def max_context(self) -> int:
        return self.total - self.reserve_output

    def fits(self, messages) -> bool:
        return self.used(messages) <= self.max_context

    def used(self, messages) -> int:
        return sum(m.tokens for m in messages)


def trim_window(messages, budget):
    kept = [m for m in messages if m.role == "system"]
    for m in reversed(messages):
        if m.role == "system":
            continue
        if budget.fits([m] + kept):
            kept.insert(0, m)
        else:
            break
    dropped = len(messages) - len(kept)
    return kept, dropped


def make_summary(messages, max_chars: int = 120) -> str:
    parts = []
    for m in messages:
        first = m.content.split("。")[0]
        parts.append(f"{m.role}:{first}")
    text = ";".join(parts)
    return text[:max_chars]


class SummaryBuffer:
    """摘要缓冲:攒够一批旧消息就压成一条摘要消息。"""
    def __init__(self, max_chars: int = 120):
        self.max_chars = max_chars
        self.text = ""

    def fold(self, messages) -> int:
        if self.text:
            messages = messages + [Message("system", self.text)]
        self.text = make_summary(messages, self.max_chars)
        return len(messages)

    def as_message(self) -> Message:
        return Message("system", "【过往摘要】" + self.text)


def importance_score(m, index: int, total: int) -> float:
    if m.role == "system":
        return 1000.0
    base = {"tool": 80.0, "user": 60.0, "assistant": 40.0}.get(m.role, 30.0)
    recency = 20.0 * index / max(total, 1)
    size = min(m.tokens * 0.5, 30.0)
    return base + recency + size


def evict_low_importance(messages, budget):
    """淘汰低价值消息:反复弹出重要性最低且非 system 的一条。"""
    kept = list(messages)
    victims = []
    while not budget.fits(kept):
        candidates = [i for i, m in enumerate(kept) if m.role != "system"]
        idx = min(candidates, key=lambda i: (importance_score(kept[i], i, len(kept)), kept[i].content))
        victims.append(kept.pop(idx).content[:16])
    return kept, victims


def recover_overflow(history, budget):
    if budget.fits(history):
        return history, [], 0
    current = list(history)
    actions = []
    folded = 0
    summary = SummaryBuffer(max_chars=120)
    old = current[1:-4]
    if old:
        folded = summary.fold(old)
        current = current[:1] + current[-4:] + [summary.as_message()]
        actions.append(f"摘要折叠 {folded} 条: {summary.text[:20]}…")
    if not budget.fits(current):
        kept, victims = evict_low_importance(current, budget)
        for v in victims:
            actions.append(f"淘汰低价值消息: {v}")
        current = kept
    if not budget.fits(current):
        kept, dropped = trim_window(current, budget)
        actions.append(f"窗口截断兜底:丢 {dropped} 条")
        current = kept
    if not budget.fits(current):
        raise ValueError("三级处置后仍装不进窗口")
    return current, actions, folded


def main() -> None:
    budget = TokenBudget(total=900, reserve_output=760)
    history = [
        Message("system", "你是Agent 运行时底座,负责在窗口溢出时逐级恢复。"),
        Message("user", "第1轮:报告普通成员分布。"),
        Message("assistant", "普通成员聚于东西两谷。"),
        Message("user", "第2轮:灵田收成如何?"),
        Message("assistant", "灵田收成尚可,未有欠收。"),
        Message("user", "第3轮:模型服务状态如何?"),
        Message("assistant", "丹模型服务候稳定,可炼上品丹。"),
        Message("user", "第4轮:请报告监控系统的耗材与更换周期,并给出上月消耗明细。"),
        Message("assistant", "监控系统每月耗预算点三百枚,上月更换监控探针两块。"),
        Message("user", "第5轮:请报告资料室的规模与新增藏书量。"),
        Message("assistant", "资料室现有藏书十二万卷,上月新增三百卷。"),
    ]
    current, actions, folded = recover_overflow(history, budget)
    print("[处置]")
    for a in actions:
        print(f"  {a}")
    print(f"本轮折叠 {folded} 条,淘汰 {len([a for a in actions if a.startswith('淘汰')])} 条,留存 {len(current)} 条,用量 {budget.used(current)} / {budget.max_context} token")


if __name__ == "__main__":
    main()
