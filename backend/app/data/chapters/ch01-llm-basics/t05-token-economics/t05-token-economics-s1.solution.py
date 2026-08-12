"""星澈助手 · 成本仪表盘 v0.1:用 tiktoken 给文本精确数 token。
这是全章收尾项目的第一块砖——要数得清,才守得住。
"""
import tiktoken

# cl100k 的切分正则:先把文本切成"字母串/数字串/符号串",再在块内做 BPE 合并
PAT_STR = r"""(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"""
# 离线降级词表:把星澈助手高频词注册成整词,贴近真实 BPE 的计数手感
FALLBACK_WORDS = ["星澈助手", "成本", "仪表盘", "预算", "守卫", "会话", "报表", "助手", "的", "了", "你", "好", "请", "问", "是", "我", "一个", "回复", "用户", "系统"]
CHAT_OVERHEAD = 4  # 每条 chat 消息的 role 等包装开销(教学近似值)


def build_encoding() -> tiktoken.Encoding:
    """优先加载真实的 cl100k_base;离线沙箱里降级为自注册的最小 BPE 编码。"""
    try:
        return tiktoken.get_encoding("cl100k_base")  # 首次使用需联网下载词表
    except Exception:
        # 降级方案:256 个字节做底,再为高频词建立逐级字节合并链
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
    """代币尺:统管编码对象,文本和消息都从这里过,便于全局替换编码。"""

    def __init__(self) -> None:
        self.encoding = build_encoding()

    def count_text(self, text: str) -> int:
        """数一段纯文本的 token 数。"""
        return len(self.encoding.encode(text))

    def count_messages(self, messages: list[dict]) -> int:
        """数一组 chat 消息的 token 数(含每条消息的包装开销)。"""
        return sum(CHAT_OVERHEAD + self.count_text(m["content"]) for m in messages)


def main() -> None:
    meter = TokenMeter()
    print(f"[星澈助手] 当前编码: {meter.encoding.name} (词表大小 {meter.encoding.n_vocab})")
    ids = meter.encoding.encode("星澈助手")
    print(f"[星澈助手] '星澈助手' 被切成 {len(ids)} 个 token,id = {ids}")
    print("[星澈助手] 字符数 vs token 数:")
    samples = ["星澈助手的成本仪表盘", "预算守卫已就位", "请帮我算一下这次会话的预算"]
    for text in samples:
        print(f"  {len(text):>2} 字符 -> {meter.count_text(text):>2} tokens | {text}")
    messages = [
        {"role": "system", "content": "你是星澈助手内置的成本助手。"},
        {"role": "user", "content": "请帮我算一下这次会话的预算"},
    ]
    total = meter.count_messages(messages)
    print(f"[星澈助手] 本组消息共 {total} tokens (每条另含 {CHAT_OVERHEAD} tokens 包装开销)")


if __name__ == "__main__":
    main()
