"""Agent 运行时底座 · s1:预算先行——给每条消息称重

Agent 的上下文窗口不是无限的,消息装多了就会溢出、截断甚至报错。
本步为「Agent 运行时底座」打地基:用启发式算法估算每条消息的 token 占用,
再把预算、输出预留与可用窗口之间的账目算清楚。"""


# === 学习契约（面向学生）===
# 本节目标：预算先行:启发式称重与预算账本。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `heuristic_tokens(text: str) -> int`：输入为签名中的参数；输出为 `int`。用途：启发式估算 token 数:CJK 每字 1 token,ASCII 每 4 字符 1 token。
#   - `print_ledger(budget: TokenBudget, messages) -> None`：输入为签名中的参数；输出为 `None`。用途：打印上下文账目:总预算、窗口、逐条占用与剩余空间。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Message`：承载本节状态/数据；重点方法：见类定义。
#   - `TokenBudget`：承载本节状态/数据；重点方法：used, remaining, fits。
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
        # TODO: 创建时自动估算 token 占用并存入 self.tokens
        # 提示: self.tokens = heuristic_tokens(self.content)
        raise NotImplementedError("__post_init__ 尚未实现:请按 TODO 提示完成 token 称重")


class TokenBudget:
    """上下文预算:总预算、输出预留与可用上下文窗口。"""

    def __init__(self, total: int, reserve_output: int):
        self.total = total
        self.reserve_output = reserve_output
        self.max_context = total - reserve_output

    def used(self, messages) -> int:
        return sum(m.tokens for m in messages)

    def remaining(self, messages) -> int:
        # TODO: 返回窗口剩余空间,即 max_context 减去已占用
        # 提示: return self.max_context - self.used(messages)
        raise NotImplementedError("remaining 尚未实现:请按 TODO 提示计算剩余空间")

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
        Message("system", "你是Agent 运行时底座的守门人,负责守护一座校园项目的运转。"),
        Message("user", "请汇报校园项目今日的运行资源收支情况,并给出三条建议。"),
        Message("assistant", "遵命。今日运行资源收入 5200,支出 3100,结余 2100。"),
        Message("user", "结余部分建议怎么处理?请说得详细一些。"),
        Message("assistant", "建议:一扩充内容制作环境,二修缮监控系统,三储备过冬预算点。"),
    ]
    print_ledger(budget, history)


if __name__ == "__main__":
    main()
