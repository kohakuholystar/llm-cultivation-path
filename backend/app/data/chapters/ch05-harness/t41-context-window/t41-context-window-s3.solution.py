"""乾坤圈 · s3:滚动摘要——旧对话压成一行浓缩信息

对话越长,历史越重,窗口迟早被撑爆。与其把旧消息原样搬进窗口,
不如把最旧的一批先压成一句话摘要,再用这条摘要代表它们。
本步实现 make_summary:把多条旧消息浓缩成一行中文摘要。"""
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
        first = m.content.split("。")[0]
        parts.append(f"{m.role}:{first}")
    text = ";".join(parts)
    return text[:max_chars]


class SummaryBuffer:
    """摘要缓冲:攒够一批旧消息就压成一条摘要消息。"""
    def __init__(self, max_chars: int = 100):
        self.max_chars = max_chars
        self.text = ""

    def fold(self, messages) -> int:
        if self.text:
            messages = messages + [Message("system", self.text)]
        self.text = make_summary(messages, self.max_chars)
        return len(messages)

    def as_message(self) -> Message:
        return Message("system", "【过往摘要】" + self.text)


def main() -> None:
    budget = TokenBudget(total=900, reserve_output=700)
    history = [
        Message("system", "你是乾坤圈,负责把旧对话压缩成摘要。"),
        Message("user", "第1轮:灵脉吞吐几何?"),
        Message("assistant", "灵脉每日吞吐三千灵石。"),
        Message("user", "第2轮:丹炉火候如何?"),
        Message("assistant", "丹炉火候稳定,可炼上品丹。"),
        Message("user", "第3轮:护山大阵运转正常吗?"),
        Message("assistant", "护山大阵一切正常,无破损。"),
    ]
    summary = SummaryBuffer(max_chars=100)
    folded = summary.fold(history[1:4])
    print(f"折叠 {folded} 条,摘要: {summary.text}")
    current = history[:1] + history[4:] + [summary.as_message()]
    print(f"压缩后 {len(current)} 条 + 1 条摘要,用量 {budget.used(current)} / {budget.max_context} token")


if __name__ == "__main__":
    main()
