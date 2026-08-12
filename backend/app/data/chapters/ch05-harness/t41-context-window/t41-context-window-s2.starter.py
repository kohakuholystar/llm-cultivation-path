"""Agent 运行时底座 · s2:滑动窗口——塞不下的历史整体裁剪

预算定好了,可对话一长,窗口照样会撑爆。本步实现「滑动窗口」:
从最新往回保留消息,system 指令永远在,塞不下的旧消息整批丢弃,
保证每次请求都装得进预算。"""


# === 学习契约（面向学生）===
# 本节目标：滑动窗口:旧消息整段让位。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `heuristic_tokens(text: str) -> int`：输入为签名中的参数；输出为 `int`。用途：启发式估算 token 数:CJK 每字 1 token,ASCII 每 4 字符 1 token。
#   - `trim_window(messages, budget) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：滑动窗口裁剪:system 必留,从最新往最旧收,塞不下就停。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Message`：承载本节状态/数据；重点方法：见类定义。
#   - `TokenBudget`：承载本节状态/数据；重点方法：used, fits。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
    # TODO: 对剩余消息按从新到旧逐个尝试,能装下就插到 kept 最前,装不下就 break
    # 提示: for m in reversed(messages[len(kept):]):若 budget.fits([m] + kept)
    #       则 kept.insert(0, m),否则 break
    raise NotImplementedError("trim_window 尚未实现:请按 TODO 提示完成滑动窗口裁剪")
    return kept, len(messages) - len(kept)


def main() -> None:
    budget = TokenBudget(total=900, reserve_output=750)
    history = [
        Message("system", "你是Agent 运行时底座,负责在有限窗口里保住关键对话。"),
        Message("user", "第1轮:请评估校园项目运行资源枯竭的风险等级。"),
        Message("assistant", "风险等级为高:网络受损三成,且恢复速度远低于消耗。"),
        Message("user", "第2轮:高风险的依据是什么?把数据列出来。"),
        Message("assistant", "依据:运行资源入不敷出已连续九个月,库存仅剩两成。"),
        Message("user", "第3轮:库存两成还能支撑多久?给出估算。"),
        Message("assistant", "按当前消耗速度,预计还能支撑约四个月,须尽快行动。"),
        Message("user", "第4轮:请把治理方案按紧急程度排序。"),
        Message("assistant", "排序:一修网络,二暂停非必要任务,三引援,四扩充工作流。"),
    ]
    kept, dropped = trim_window(history, budget)
    print(f"截断后 {len(kept)} 条,丢弃 {dropped} 条,用量 {budget.used(kept)} / {budget.max_context} token")


if __name__ == "__main__":
    main()
