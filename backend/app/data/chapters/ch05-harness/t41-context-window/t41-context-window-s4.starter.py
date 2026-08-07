"""乾坤圈 · s4:重要性淘汰——低价值消息逐个让位

摘要擅长压缩旧对话,但有些消息不该被压扁:工具返回、最新指令信息密度太高。
本步换一条思路:给每条消息打重要性分,窗口放不下时就弹出得分最低的,
直到装下为止——低价值消息逐个让位。"""
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
    reserve_output: int = 850

    @property
    def max_context(self) -> int:
        return self.total - self.reserve_output

    def fits(self, messages) -> bool:
        return self.used(messages) <= self.max_context

    def used(self, messages) -> int:
        return sum(m.tokens for m in messages)


def importance_score(m, index: int, total: int) -> float:
    """重要性打分:角色基础分 + 时新度加分 + 内容量加分。"""
    if m.role == "system":
        return 1000.0
    base = {"tool": 80.0, "user": 60.0, "assistant": 40.0}.get(m.role, 30.0)
    recency = 20.0 * index / max(total, 1)
    size = min(m.tokens * 0.5, 30.0)
    # TODO: 返回总分,即 base + recency + size
    # 提示: recency 与 size 已算好,直接 return base + recency + size
    raise NotImplementedError("importance_score 尚未实现:请按 TODO 提示返回总分")


def evict_low_importance(messages, budget):
    """淘汰低价值消息:反复弹出重要性最低且非 system 的一条。"""
    kept = list(messages)
    victims = []
    while not budget.fits(kept):
        # TODO: 枚举 kept 中 role != "system" 的索引,弹出重要性最低者的内容前 16 字
        # 提示: candidates = [i for i, m in enumerate(kept) if m.role != "system"];
        #       idx = min(candidates, key=lambda i: (importance_score(kept[i], i, len(kept)), kept[i].content));
        #       victims.append(kept.pop(idx).content[:16])
        raise NotImplementedError("evict_low_importance 尚未实现:请按 TODO 提示完成最低分淘汰")
    return kept, victims


def main() -> None:
    budget = TokenBudget(total=900, reserve_output=850)
    history = [
        Message("system", "你是乾坤圈,负责在窗口紧张时淘汰低价值消息。"),
        Message("user", "第1轮:灵药库存几何?"),
        Message("assistant", "灵药库存三千二百株。"),
        Message("user", "第2轮:库房何时盘点?"),
        Message("assistant", "库房每月初一盘点。"),
        Message("user", "第3轮:外门弟子几何?"),
        Message("assistant", "外门弟子三千人。"),
        Message("user", "第4轮:藏经阁开放时间?"),
        Message("assistant", "藏经阁每日辰时开放。"),
    ]
    kept, victims = evict_low_importance(history, budget)
    print(f"被淘汰 {len(victims)} 条:" + " ".join(f"[{v}]" for v in victims))
    print(f"留存 {len(kept)} 条,用量 {budget.used(kept)} / {budget.max_context} token")


if __name__ == "__main__":
    main()
