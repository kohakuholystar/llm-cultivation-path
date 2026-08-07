"""乾坤圈 · s6:总装——黑盒上下文管理器

前五步的散件(称重、滚动摘要、重要性评分、淘汰、溢出恢复)
在本步拧成一根完整的轴:外部只调用 add / snapshot / stats
三个动作,内部自动称重、自动折叠、自动淘汰,窗口永不溢出。"""

from dataclasses import dataclass
import math
import re


CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def heuristic_tokens(text: str) -> int:
    # TODO: 用启发式算法估算 token 数:CJK 每字 1 token,ASCII 每 4 字符 1 token
    # 提示: cjk = len(CJK_RE.findall(text));
    #       rest = re.sub(r"\s", "", CJK_RE.sub("", text));
    #       return max(cjk + math.ceil(len(rest) / 4), 1)
    raise NotImplementedError("heuristic_tokens 尚未实现:请按 TODO 提示完成 token 估算")


@dataclass
class Message:
    """一条带权重的对话消息。"""
    role: str
    content: str
    tokens: int = 0

    def __post_init__(self):
        if self.tokens <= 0:
            # TODO: 调用 heuristic_tokens 为内容称重并存入 self.tokens
            # 提示: self.tokens = heuristic_tokens(self.content)
            raise NotImplementedError("__post_init__ 尚未实现:请按 TODO 提示完成称重")


@dataclass
class TokenBudget:
    """上下文预算:总容量与输出预留。"""
    total: int = 900
    reserve_output: int = 760

    @property
    def max_context(self) -> int:
        # TODO: 返回可给对话使用的窗口大小,即总量减去输出预留
        # 提示: return self.total - self.reserve_output
        raise NotImplementedError("max_context 尚未实现:请按 TODO 提示计算窗口上限")

    def used(self, messages: list) -> int:
        # TODO: 统计全部消息的 token 用量之和
        # 提示: return sum(m.tokens for m in messages)
        raise NotImplementedError("used 尚未实现:请按 TODO 提示统计用量")

    def fits(self, messages: list) -> bool:
        # TODO: 判断用量是否仍在窗口内
        # 提示: return self.used(messages) <= self.max_context
        raise NotImplementedError("fits 尚未实现:请按 TODO 提示判断是否装得下")


def make_summary(messages: list, max_chars: int = 100) -> str:
    # TODO: 把消息拼成一行文本,超长截断到 max_chars
    # 提示: pairs = [f"{m.role}:{m.content}" for m in messages];
    #       text = "；".join(pairs);return text[:max_chars]
    raise NotImplementedError("make_summary 尚未实现:请按 TODO 提示拼接摘要")


class SummaryBuffer:
    def __init__(self, max_chars: int = 100):
        self.max_chars = max_chars
        self.text = ""

    def fold(self, messages: list) -> int:
        # TODO: 已有旧摘要时把它作为 system 消息接到最前,再压进 self.text,返回折叠条数
        # 提示: combined = [Message("system", self.text)] if self.text else [];
        #       self.text = make_summary(combined + messages, self.max_chars);
        #       return len(combined + messages)
        raise NotImplementedError("fold 尚未实现:请按 TODO 提示完成折叠")


def importance_score(m: Message, index: int, total: int) -> float:
    # TODO: 按角色、位置与长度打分,分越低越先淘汰
    # 提示: base = 0.0 if m.role == "system" else 10.0;
    #       return base + 20.0 * index / max(total, 1) + min(m.tokens * 0.5, 30.0)
    raise NotImplementedError("importance_score 尚未实现:请按 TODO 提示完成打分")


def evict_lowest(messages: list, budget: TokenBudget, actions: list) -> int:
    # TODO: 反复淘汰分数最低的非 system 消息,把动作记入 actions,返回淘汰条数
    # 提示: evicted = 0;
    #       while not budget.fits(messages):
    #         candidates = [m for m in messages[1:] if m.role != "system"];无候选则 break;
    #         scored = sorted((importance_score(m, i, len(candidates)), m)
    #                         for i, m in enumerate(candidates), key=lambda p: p[0]);
    #         victim = scored[0][1];messages.remove(victim);evicted += 1;
    #         actions.append(f"淘汰低价值消息 {victim.content[:8]}")
    #       return evicted
    raise NotImplementedError("evict_lowest 尚未实现:请按 TODO 提示完成淘汰循环")


def recover_overflow(current: list, budget: TokenBudget, summary: SummaryBuffer) -> tuple:
    # TODO: 先折叠最旧的一批旧消息成滚动摘要;仍溢出就调用 evict_lowest 淘汰;再溢出直接抛错
    # 提示: actions = [];folded = 0;
    #       if not budget.fits(current) and len(current) > 2:
    #         old = current[1:-4] if len(current) > 5 else [];有 old 则 folded = summary.fold(old),
    #         从 current 移除各旧消息,insert(1, Message("system", summary.text)),
    #         actions.append(f"摘要折叠 {folded} 条");
    #       evict_lowest(current, budget, actions);
    #       if not budget.fits(current): raise ValueError("窗口仍然溢出");
    #       return current, actions, folded
    raise NotImplementedError("recover_overflow 尚未实现:请按 TODO 提示完成恢复链")


class ContextManager:
    """乾坤圈总装:对外只暴露 add / snapshot / stats 三个动作。"""

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
            # TODO: 调用 recover_overflow 处置溢出,累计折叠与淘汰计数,回写消息并打印处置记录
            # 提示: current, actions, folded = recover_overflow(self.snapshot(), self.budget, self.summary);
            #       self.folded += folded;
            #       self.evicted += len([a for a in actions if a.startswith("淘汰")]);
            #       self.messages = current;逐条 print(f"    [恢复] {a}")
            raise NotImplementedError("add 尚未实现:请按 TODO 提示完成溢出处置")

    def stats(self) -> str:
        # TODO: 返回一句统计:折叠/淘汰条数与当前用量
        # 提示: return (f"统计: 折叠 {self.folded} 条,淘汰 {self.evicted} 条,"
        #               f"当前用量 {self.budget.used(self.snapshot())} / {self.budget.max_context} token")
        raise NotImplementedError("stats 尚未实现:请按 TODO 提示返回统计")


def main():
    cm = ContextManager()
    msgs = [
        Message("system", "你是乾坤圈,负责管理对话窗口。"),
        Message("user", "第1轮:请汇报今日灵气收支情况。附上月对比与结余明细。"),
        Message("assistant", "收入五千二,支出三千一,结余两千一。对比上月整体健康,无异常波动。"),
        Message("tool", "tool_result: 灵脉图已生成,存于藏经阁第三层。附各坊产量明细。"),
        Message("user", "第2轮:结余如何处置?"),
        Message("assistant", "建议三条:一扩丹房,二修大阵,三储备灵石。"),
        Message("user", "第3轮:扩丹房需多少灵石?请估算回本周期,并对比现有丹房产量与矿石品质,给出灵矿储备明细。"),
    ]
    for m in msgs:
        cm.add(m)
        print(f"加入[{m.role}]后:消息 {len(cm.snapshot())} 条(含摘要),用量 {cm.budget.used(cm.snapshot())} / {cm.budget.max_context} token")
    print(cm.stats())


if __name__ == "__main__":
    main()
