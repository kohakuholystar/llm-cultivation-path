"""灵讯通 · 成本仪表盘 v0.3:预算守卫——超支就拒绝调用的装饰器。"""
import functools
import tiktoken
from dataclasses import dataclass

PAT_STR = r"""(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"""
FALLBACK_WORDS = ["灵讯通", "成本", "仪表盘", "预算", "守卫", "会话", "报表", "助手", "的", "了", "你", "好", "请", "问", "是", "我", "一个", "回复", "用户", "系统"]
CHAT_OVERHEAD = 4
MODEL_NAME = "deepseek-v4-pro"


def build_encoding() -> tiktoken.Encoding:
    """优先加载真实的 cl100k_base;离线沙箱里降级为自注册的最小 BPE 编码。"""
    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        ranks, nxt = {bytes([i]): i for i in range(256)}, 256
        for word in FALLBACK_WORDS:
            cur = b""
            for byte in word.encode("utf-8"):
                cur += bytes([byte])
                if cur not in ranks:
                    ranks[cur] = nxt
                    nxt += 1
        return tiktoken.Encoding(name="lingxun-mini", pat_str=PAT_STR, mergeable_ranks=ranks, special_tokens={})


class TokenMeter:
    """代币尺:统管编码对象,文本和消息都从这里过。"""

    def __init__(self) -> None:
        self.encoding = build_encoding()

    def count_text(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def count_messages(self, messages: list[dict]) -> int:
        return sum(CHAT_OVERHEAD + self.count_text(m["content"]) for m in messages)


@dataclass(frozen=True)
class ModelPricing:
    """单模型费率表,单位:元 / 百万 tokens。"""

    model: str
    input_per_million: float
    output_per_million: float
    cached_input_per_million: float = 0.0


PRICING_TABLE = {MODEL_NAME: ModelPricing(MODEL_NAME, 2.0, 8.0, 0.5)}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int, cached_tokens: int = 0) -> float:
    """按费率表估算一次调用的成本(元)。"""
    if model not in PRICING_TABLE:
        raise ValueError(f"费率表中没有模型: {model}")
    p = PRICING_TABLE[model]
    fresh = max(prompt_tokens - cached_tokens, 0)
    per_million = (fresh * p.input_per_million
                   + cached_tokens * p.cached_input_per_million
                   + completion_tokens * p.output_per_million)
    return per_million / 1_000_000


class BudgetExceededError(RuntimeError):
    """预算守卫拒绝调用时抛出。"""


def budget_guard(max_budget: float, meter: TokenMeter, model: str = MODEL_NAME):
    """装饰器工厂:给 LLM 调用装上预算守卫——超支拒付,放行记账。"""
    state = {"spent": 0.0, "rejected": 0}  # 闭包账目:累计花费与拒绝数

    def decorator(func):
        @functools.wraps(func)
        def wrapper(messages: list[dict], max_tokens: int = 200):
            # TODO: 超支判断与记账。
            # 提示: projected = estimate_cost(model, meter.count_messages(messages), max_tokens)
            #       if state["spent"] + projected > max_budget: 拒绝数 +1 并 raise BudgetExceededError(...)
            #       放行: result = func(messages, max_tokens=max_tokens), 然后 state["spent"] += result["cost"]
            pass

        wrapper.state = state
        return wrapper

    return decorator


def mock_chat(messages: list[dict], max_tokens: int = 200) -> dict:
    """离线假 LLM:用固定回复模拟 deepseek-v4-pro,返回真实感 usage。"""
    prompt_tokens = TokenMeter().count_messages(messages)
    completion_tokens = min(32, max_tokens)
    return {
        "reply": "收到,灵讯通成本助手已记录你的请求。",
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost": estimate_cost(MODEL_NAME, prompt_tokens, completion_tokens),
    }


def main() -> None:
    meter = TokenMeter()
    guarded_chat = budget_guard(max_budget=0.002, meter=meter)(mock_chat)
    prompts = ["帮我写一句灵讯通的欢迎语", "再写一句口号", "继续写第三条"]
    for prompt in prompts:
        try:
            result = guarded_chat([{"role": "user", "content": prompt}], max_tokens=200)
            print(f"[放行] {prompt} -> {result['reply']} (本次 ¥{result['cost']:.6f})")
        except BudgetExceededError as exc:
            print(f"[拒绝] {prompt} -> {exc}")
    print(f"[灵讯通] 守卫账目: 已花 ¥{guarded_chat.state['spent']:.6f},拒绝 {guarded_chat.state['rejected']} 次")


if __name__ == "__main__":
    main()
