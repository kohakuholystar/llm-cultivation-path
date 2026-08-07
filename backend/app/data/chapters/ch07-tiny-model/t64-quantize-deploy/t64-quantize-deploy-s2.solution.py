"""袖里乾坤 · s2:量化推理引擎

在 s1 量化权重之上实现 INT8 整数推理链路:动态量化激活、
整数矩阵乘、一次反量化,并与 FP32 全精度前向对比 logits,
让量化误差变得可见、可控。
"""
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
    x = qw["embed_q"][tokens].mean(axis=0) * qw["embed_scale"]   # 平均嵌入回到浮点
    x_q, sx = dyn_quant(x)
    h_int = x_q.astype(np.int32) @ qw["hidden_q"].astype(np.int32)   # 整数累积!
    h = np.tanh(h_int * (sx * qw["hidden_scale"]))
    h_q, sh = dyn_quant(h)
    logits_int = h_q.astype(np.int32) @ qw["out_q"].astype(np.int32)
    return logits_int * (sh * qw["out_scale"])


def main() -> None:
    weights = make_weights()
    q = quantize_model(weights)
    tokens = tokens_of("quantum")
    fp = forward_fp32(weights, tokens)
    it = forward_int8(q, tokens)
    print(f"[输入] token 序列: {tokens}")
    print(f"[FP32] logits: {np.round(fp, 3).tolist()}")
    print(f"[INT8] logits: {np.round(it, 3).tolist()}")
    print(f"[对比] logits 最大偏差 = {float(np.max(np.abs(fp - it))):.4f}")


if __name__ == "__main__":
    main()
