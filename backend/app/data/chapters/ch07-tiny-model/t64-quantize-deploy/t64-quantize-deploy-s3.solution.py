"""袖里乾坤 · s3:推理加速对比

量化到底快了多少?本步给 FP32 与 INT8 两条推理链路架起公平的
计时擂台:预热 → 多次计时取平均 → 计算加速比。小矩阵场景下
INT8 未必更快,本步练的是「可复现的测量方法」这一工程基本功。
"""
import time

import numpy as np

np.random.seed(42)

VOCAB = list("abcdefghijklmnopqrstuvwxyz ")
V, H = len(VOCAB), 16
CONFIG = {"vocab": V, "hidden": H}


def make_weights() -> dict:
    """蒸馏产物权重:嵌入/隐藏/输出三矩阵,演示用随机权重。"""
    rand = lambda *s: np.random.randn(*s).astype(np.float32) * 0.1
    return {"embed": rand(V, H), "hidden": rand(H, H), "out": rand(H, V)}


def quantize_tensor(w: np.ndarray) -> tuple:
    """对称 int8 量化:返回 (int8 权重, scale)。"""
    scale = float(np.max(np.abs(w))) / 127.0
    return np.round(w / scale).astype(np.int8), scale


def quantize_model(weights: dict) -> dict:
    """逐张量量化,键名加上 _q / _scale 后缀。"""
    out = {}
    for name, w in weights.items():
        qw, scale = quantize_tensor(w)
        out[name + "_q"] = qw
        out[name + "_scale"] = scale
    return out


def tokens_of(text: str) -> list[int]:
    """字符串 → 词表下标列表,未知字符一律映射为空格(0 号)。"""
    return [VOCAB.index(ch) if ch in VOCAB else 0 for ch in text]


def dyn_quant(x: np.ndarray) -> tuple:
    """动态量化激活:返回 (int8 向量, scale)。"""
    scale = float(np.max(np.abs(x))) / 127.0
    return np.round(x / scale).astype(np.int8), scale


def forward_fp32(weights: dict, tokens: list[int]) -> np.ndarray:
    """全精度前向:平均嵌入 → tanh 隐藏层 → 输出 logits。"""
    x = weights["embed"][tokens].mean(axis=0)
    h = np.tanh(x @ weights["hidden"])
    return h @ weights["out"]


def forward_int8(qw: dict, tokens: list[int]) -> np.ndarray:
    """整数推理:激活与权重都落到 int8,矩阵乘在 int32 累加器完成。"""
    x = qw["embed_q"][tokens].mean(axis=0) * qw["embed_scale"]
    x_q, sx = dyn_quant(x)
    h_int = x_q.astype(np.int32) @ qw["hidden_q"].astype(np.int32)
    h = np.tanh(h_int * (sx * qw["hidden_scale"]))
    h_q, sh = dyn_quant(h)
    logits_int = h_q.astype(np.int32) @ qw["out_q"].astype(np.int32)
    return logits_int * (sh * qw["out_scale"])


def bench(fn, tokens: list[int], rounds: int = 200) -> float:
    """返回单次推理的平均耗时(毫秒):先预热,再多次计时。"""
    for _ in range(20):
        fn(tokens)   # 预热:让缓存与分配器进入稳态
    t0 = time.perf_counter()
    for _ in range(rounds):
        fn(tokens)
    return (time.perf_counter() - t0) / rounds * 1000.0


def main() -> None:
    weights = make_weights()
    q = quantize_model(weights)
    tokens = tokens_of("quantum computation")
    fp_ms = bench(lambda t: forward_fp32(weights, t), tokens)
    int8_ms = bench(lambda t: forward_int8(q, t), tokens)
    speedup = fp_ms / int8_ms
    print(f"[FP32] 平均耗时 {fp_ms:.3f} ms/次")
    print(f"[INT8] 平均耗时 {int8_ms:.3f} ms/次")
    print(f"[结论] 量化推理速度 x{speedup:.2f}(>1 为加速,<1 属正常)")
    print("[提示] 真实加速依赖硬件 INT8 SIMD 指令;numpy 小矩阵场景以方法正确为先")


if __name__ == "__main__":
    main()
