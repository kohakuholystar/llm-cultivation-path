"""灵讯通 · 成本仪表盘 v1.0:多会话用量统计报表——章项目收官。"""
import functools
import tiktoken
from dataclasses import dataclass

PAT_STR = r"""(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"""
FALLBACK_WORDS = ["灵讯通", "成本", "仪表盘", "预算", "守卫", "会话", "报表", "助手", "的", "了", "你", "好", "请", "问", "是", "我", "一个", "回复", "用户", "系统"]
CHAT_OVERHEAD = 4  # 每条 chat 消息的包装开销(教学近似值)
MODEL_NAME = "deepseek-v4-pro"


def build_encoding() -> tiktoken.Encoding:
    try:
        return tiktoken.get_encoding("cl100k_base")  # 首次使用需联网下载词表
    except Exception:  # 离线降级:256 字节打底,为高频词建逐级字节合并链(与 v0.1 同口径)
        prefixes = [w.encode()[:i] for w in FALLBACK_WORDS for i in range(2, len(w.encode()) + 1)]
        ranks = {bytes([i]): i for i in range(256)}
        ranks.update({p: 256 + k for k, p in enumerate(dict.fromkeys(prefixes))})
        return tiktoken.Encoding(name="lingxun-mini", pat_str=PAT_STR, mergeable_ranks=ranks, special_tokens={})


class TokenMeter:  # 代币尺:统管编码对象,文本和消息都从这里过

    def __init__(self) -> None:
        self.encoding = build_encoding()

    def count_text(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def count_messages(self, messages: list[dict]) -> int:
        return sum(CHAT_OVERHEAD + self.count_text(m["content"]) for m in messages)


@dataclass(frozen=True)
class ModelPricing:  # 单模型费率表,单位:元 / 百万 tokens;frozen 防半路改价

    model: str
    input_per_million: float
    output_per_million: float
    cached_input_per_million: float = 0.0


PRICING_TABLE = {MODEL_NAME: ModelPricing(MODEL_NAME, 2.0, 8.0, 0.5)}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int, cached_tokens: int = 0) -> float:
    if model not in PRICING_TABLE:
        raise ValueError(f"费率表中没有模型: {model}")
    p = PRICING_TABLE[model]
    return (max(prompt_tokens - cached_tokens, 0) * p.input_per_million  # 未命中缓存的输入走全价
            + cached_tokens * p.cached_input_per_million + completion_tokens * p.output_per_million) / 1_000_000


class BudgetExceededError(RuntimeError): ...  # 预算守卫拒绝调用时抛出,调用方必须显式处理


@dataclass
class UsageRecord:  # 一条不可变事实:某会话某次调用的真实用量与成本

    session_id: str
    prompt_tokens: int
    completion_tokens: int
    cost: float


class UsageLedger:
    """多会话用量账本:只管存事实与聚合,不管价格怎么算。"""

    def __init__(self) -> None:
        self._records: list[UsageRecord] = []

    def add(self, record: UsageRecord) -> None: self._records.append(record)

    def total_cost(self) -> float: return sum(r.cost for r in self._records)

    def by_session(self) -> dict:
        """按会话归集:调用次数、token 总量、成本合计。"""
        agg = {}
        for r in self._records:
            s = agg.setdefault(r.session_id, {"calls": 0, "tokens": 0, "cost": 0.0})
            s["calls"] += 1
            s["tokens"] += r.prompt_tokens + r.completion_tokens
            s["cost"] += r.cost
        return agg


def budget_guard(max_budget: float, meter: TokenMeter, ledger: UsageLedger = None, model: str = MODEL_NAME):
    state = {"spent": 0.0, "rejected": 0}  # 闭包账目:累计花费与拒绝数

    def decorator(func):
        @functools.wraps(func)
        def wrapper(messages: list[dict], max_tokens: int = 200, session_id: str = "default"):
            projected = estimate_cost(model, meter.count_messages(messages), max_tokens)
            if state["spent"] + projected > max_budget:
                state["rejected"] += 1
                raise BudgetExceededError(f"本次预计 ¥{projected:.6f},将超 ¥{max_budget:.4f} 预算,已拒绝")
            result = func(messages, max_tokens=max_tokens)
            state["spent"] += result["cost"]
            if ledger is not None:  # 只记放行的调用:被拒绝的一分钱没花
                ledger.add(UsageRecord(session_id, result["prompt_tokens"], result["completion_tokens"], result["cost"]))
            return result

        wrapper.state = state  # 暴露账目,便于仪表盘读取
        return wrapper

    return decorator


def mock_chat(messages: list[dict], max_tokens: int = 200) -> dict:
    prompt_tokens, completion_tokens = TokenMeter().count_messages(messages), min(32, max_tokens)  # 离线假 LLM
    return {"reply": "收到,灵讯通成本助手已记录你的请求。", "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "cost": estimate_cost(MODEL_NAME, prompt_tokens, completion_tokens)}


def render_report(ledger: UsageLedger, budget: float, rejected: int) -> str:
    """把账本渲染成灵讯通成本仪表盘:返回字符串,与打印解耦,便于测试。"""
    sessions = ledger.by_session()
    if not sessions: return "灵讯通 · 成本仪表盘\n暂无用量记录。"
    total, calls = ledger.total_cost(), sum(s["calls"] for s in sessions.values())  # 平均值是隐藏的异常探测器
    rows = ["灵讯通 · 成本仪表盘", f"{'会话':<6} {'调用':>2} {'tokens':>5} {'成本(元)':>10}"]
    rows += [f"{sid:<6} {s['calls']:>4} {s['tokens']:>6} {s['cost']:>13.6f}" for sid, s in sessions.items()]
    rows.append(f"总成本 ¥{total:.6f} / 预算 ¥{budget:.4f} | 共 {calls} 次调用(均 ¥{total / calls:.6f}),守卫拒绝 {rejected} 次")
    rows.append("状态: " + ("预算告急,请充值或收紧 max_tokens" if total > budget * 0.8 else "预算健康"))  # 阈值写成预算的比例
    return "\n".join(rows)

def main() -> None:
    meter, ledger, budget = TokenMeter(), UsageLedger(), 0.0025
    guarded_chat = budget_guard(max_budget=budget, meter=meter, ledger=ledger)(mock_chat)
    plan = [("客服会话", "帮我写一句灵讯通的欢迎语"), ("客服会话", "再写一句口号"), ("售后会话", "写一条退款安抚回复"), ("售后会话", "再写一条更诚恳的"), ("售后会话", "继续写第三条")]
    for session_id, prompt in plan:
        try:
            guarded_chat([{"role": "user", "content": prompt}], max_tokens=200, session_id=session_id)
        except BudgetExceededError as exc:
            print(f"[拒绝][{session_id}] {prompt} -> {exc}")  # 只演示被拦截的;放行过程见 v0.4
    print(render_report(ledger, budget=budget, rejected=guarded_chat.state["rejected"]))


if __name__ == "__main__":
    main()
