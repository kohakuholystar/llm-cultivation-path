"""Agent 运行时底座 · s3:滚动摘要——旧对话压成一行浓缩信息

对话越长,历史越重,窗口迟早被撑爆。与其把旧消息原样搬进窗口,
不如把最旧的一批先压成一句话摘要,再用这条摘要代表它们。
本步实现 make_summary:把多条旧消息浓缩成一行中文摘要。"""


# === 学习契约（面向学生）===
# 本节目标：滚动摘要:旧对话压成一行浓缩信息。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `heuristic_tokens(text: str) -> int`：输入为签名中的参数；输出为 `int`。用途：启发式估算 token 数:CJK 每字 1 token,ASCII 每 4 字符 1 token。
#   - `make_summary(messages, max_chars: int=100) -> str`：输入为签名中的参数；输出为 `str`。用途：把多条旧消息压成一行摘要:取每条的首句拼接。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Message`：承载本节状态/数据；重点方法：tokens。
#   - `TokenBudget`：承载本节状态/数据；重点方法：max_context, fits, used。
#   - `SummaryBuffer`：承载本节状态/数据；重点方法：fold, as_message。
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
    reserve_output: int = 700

    @property
    def max_context(self) -> int:
        return self.total - self.reserve_output

    def fits(self, messages) -> bool:
        return self.used(messages) <= self.max_context

    def used(self, messages) -> int:
        return sum(m.tokens for m in messages)


def make_summary(messages, max_chars: int = 100) -> str:
    """把多条旧消息压成一行摘要:取每条的首句拼接。"""
    parts = []
    for m in messages:
        # TODO: 取 m.content 按「。」切分的首句,把 f"{m.role}:{first}" 追加进 parts
        # 提示: first = m.content.split("。")[0];parts.append(f"{m.role}:{first}")
        raise NotImplementedError("make_summary 尚未实现:请按 TODO 提示逐条取首句拼接")
    text = ";".join(parts)
    return text[:max_chars]


class SummaryBuffer:
    """摘要缓冲:攒够一批旧消息就压成一条摘要消息。"""
    def __init__(self, max_chars: int = 100):
        self.max_chars = max_chars
        self.text = ""

    def fold(self, messages) -> int:
        # TODO: 已有旧摘要时把它作为 system 消息接到 messages 前面,再生成新摘要
        # 提示: if self.text: messages = messages + [Message("system", self.text)];
        #       self.text = make_summary(messages, self.max_chars);return len(messages)
        raise NotImplementedError("fold 尚未实现:请按 TODO 提示完成摘要折叠")

    def as_message(self) -> Message:
        return Message("system", "【过往摘要】" + self.text)


def main() -> None:
    budget = TokenBudget(total=900, reserve_output=700)
    history = [
        Message("system", "你是Agent 运行时底座,负责把旧对话压缩成摘要。"),
        Message("user", "第1轮:网络吞吐几何?"),
        Message("assistant", "网络每日吞吐三千预算点。"),
        Message("user", "第2轮:模型服务状态如何?"),
        Message("assistant", "丹模型服务候稳定,可炼上品丹。"),
        Message("user", "第3轮:监控系统运转正常吗?"),
        Message("assistant", "监控系统一切正常,无破损。"),
    ]
    summary = SummaryBuffer(max_chars=100)
    folded = summary.fold(history[1:4])
    print(f"折叠 {folded} 条,摘要: {summary.text}")
    current = history[:1] + history[4:] + [summary.as_message()]
    print(f"压缩后 {len(current)} 条 + 1 条摘要,用量 {budget.used(current)} / {budget.max_context} token")


if __name__ == "__main__":
    main()
