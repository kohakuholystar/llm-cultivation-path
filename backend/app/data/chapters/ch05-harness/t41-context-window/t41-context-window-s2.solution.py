"""乾坤圈 · s2:滑动窗口——塞不下的历史整体裁剪

预算定好了,可对话一长,窗口照样会撑爆。本步实现「滑动窗口」:
从最新往回保留消息,system 指令永远在,塞不下的旧消息整批丢弃,
保证每次请求都装得进预算。"""
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

    def fits(self, messages) -> bool:
        return self.used(messages) <= self.max_context


def trim_window(messages, budget):
    """滑动窗口裁剪:system 必留,从最新往最旧收,塞不下就停。"""
    kept = []
    if messages and messages[0].role == "system":
        kept.append(messages[0])
    for m in reversed(messages[len(kept):]):
        if budget.fits([m] + kept):
            kept.insert(0, m)
        else:
            break
    return kept, len(messages) - len(kept)


def main() -> None:
    budget = TokenBudget(total=900, reserve_output=750)
    history = [
        Message("system", "你是乾坤圈,负责在有限窗口里保住关键对话。"),
        Message("user", "第1轮:请评估仙山灵气枯竭的风险等级。"),
        Message("assistant", "风险等级为高:灵脉受损三成,且恢复速度远低于消耗。"),
        Message("user", "第2轮:高风险的依据是什么?把数据列出来。"),
        Message("assistant", "依据:灵气入不敷出已连续九个月,库存仅剩两成。"),
        Message("user", "第3轮:库存两成还能支撑多久?给出估算。"),
        Message("assistant", "按当前消耗速度,预计还能支撑约四个月,须尽快行动。"),
        Message("user", "第4轮:请把治理方案按紧急程度排序。"),
        Message("assistant", "排序:一修灵脉,二封山休养,三引援,四扩充阵法。"),
    ]
    kept, dropped = trim_window(history, budget)
    print(f"截断后 {len(kept)} 条,丢弃 {dropped} 条,用量 {budget.used(kept)} / {budget.max_context} token")


if __name__ == "__main__":
    main()
