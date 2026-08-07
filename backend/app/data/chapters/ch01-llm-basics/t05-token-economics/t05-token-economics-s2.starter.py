"""灵讯通 · 成本仪表盘 v0.2:给 token 标上价格——DeepSeek 费率表建模。"""
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
    # TODO: 查表计算成本 = (未命中输入 * 输入价 + 命中输入 * 缓存价 + 输出 * 输出价) / 1_000_000
    # 提示: 先 if model not in PRICING_TABLE: raise ValueError(...);
    #       未命中输入 = max(prompt_tokens - cached_tokens, 0)
    pass


def main() -> None:
    meter = TokenMeter()
    messages = [
        {"role": "system", "content": "你是灵讯通内置的成本助手。"},
        {"role": "user", "content": "请帮我算一下这次会话的预算"},
    ]
    prompt_tokens = meter.count_messages(messages)
    completion_tokens = 150
    print(f"[灵讯通] 输入 {prompt_tokens} tokens,预计输出 {completion_tokens} tokens")
    cost = estimate_cost(MODEL_NAME, prompt_tokens, completion_tokens)
    print(f"[灵讯通] 本次预估成本: ¥{cost:.6f}")
    cached_cost = estimate_cost(MODEL_NAME, prompt_tokens, completion_tokens, cached_tokens=20)
    print(f"[灵讯通] 若其中 20 tokens 命中缓存: ¥{cached_cost:.6f} (省 ¥{cost - cached_cost:.6f})")


if __name__ == "__main__":
    main()
