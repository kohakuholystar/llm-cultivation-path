"""Agent 运行时底座 · s4:重要性淘汰——低价值消息逐个让位

摘要擅长压缩旧对话,但有些消息不该被压扁:工具返回、最新指令信息密度太高。
本步换一条思路:给每条消息打重要性分,窗口放不下时就弹出得分最低的,
直到装下为止——低价值消息逐个让位。"""


# === 学习契约（面向学生）===
# 本节目标：重要性淘汰:低价值消息逐个让位。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `heuristic_tokens(text: str) -> int`：输入为签名中的参数；输出为 `int`。用途：启发式估算 token 数:CJK 每字 1 token,ASCII 每 4 字符 1 token。
#   - `importance_score(m, index: int, total: int) -> float`：输入为签名中的参数；输出为 `float`。用途：重要性打分:角色基础分 + 时新度加分 + 内容量加分。
#   - `evict_low_importance(messages, budget) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：淘汰低价值消息:反复弹出重要性最低且非 system 的一条。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Message`：承载本节状态/数据；重点方法：tokens。
#   - `TokenBudget`：承载本节状态/数据；重点方法：max_context, fits, used。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
        Message("system", "你是Agent 运行时底座,负责在窗口紧张时淘汰低价值消息。"),
        Message("user", "第1轮:参考资料库存几何?"),
        Message("assistant", "参考资料库存三千二百株。"),
        Message("user", "第2轮:库房何时盘点?"),
        Message("assistant", "库房每月初一盘点。"),
        Message("user", "第3轮:普通成员几何?"),
        Message("assistant", "普通成员三千人。"),
        Message("user", "第4轮:黑糖资料室开放时间?"),
        Message("assistant", "黑糖资料室每日每日开放时段开放。"),
    ]
    kept, victims = evict_low_importance(history, budget)
    print(f"被淘汰 {len(victims)} 条:" + " ".join(f"[{v}]" for v in victims))
    print(f"留存 {len(kept)} 条,用量 {budget.used(kept)} / {budget.max_context} token")


if __name__ == "__main__":
    main()
