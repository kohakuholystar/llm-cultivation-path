"""模型研究小组 · s1:权重落盘与 int8 量化

蒸馏出的小模型(字符级,随机演示权重)先落盘成 .npz,
再实现 int8 对称量化:算 scale、量化、反量化、评估误差。
这是模型从 32 位浮点压缩到四分之一体积的第一步。
"""
import numpy as np

np.random.seed(42)  # 固定种子:保证每个学员拿到的权重一致

VOCAB = list("abcdefghijklmnopqrstuvwxyz ")   # 词表:26 个字母 + 空格
V, H = len(VOCAB), 16                          # 词表大小、隐藏维度
CONFIG = {"vocab": V, "hidden": H}
MODEL_FILE = "tiny_model.npz"


def make_weights() -> dict:
    """蒸馏产物权重:嵌入/隐藏/输出三矩阵,演示用随机权重。"""
    rand = lambda *s: np.random.randn(*s).astype(np.float32) * 0.1
    return {"embed": rand(V, H), "hidden": rand(H, H), "out": rand(H, V)}


def quantize_tensor(w: np.ndarray) -> tuple:
    """对称 int8 量化:返回 (int8 权重, scale)。"""
    scale = float(np.max(np.abs(w))) / 127.0
    return np.round(w / scale).astype(np.int8), scale


def dequantize(q: np.ndarray, scale: float) -> np.ndarray:
    """反量化:把 int8 权重还原成浮点近似。"""
    return q * scale


def quantize_model(weights: dict) -> dict:
    """逐张量量化,键名加上 _q / _scale 后缀。"""
    out = {}
    for name, w in weights.items():
        qw, scale = quantize_tensor(w)
        out[name + "_q"] = qw
        out[name + "_scale"] = scale
    return out


def export_weights(weights: dict) -> None:
    """把原始浮点权重导出为 .npz 存档。"""
    np.savez(MODEL_FILE, **weights)
    print(f"[导出] 已保存 {MODEL_FILE},共 {len(weights)} 个张量")


def inspect_archive() -> None:
    """读回 .npz,核对张量形状,并预告量化后的体积收益。"""
    with np.load(MODEL_FILE) as data:
        total = 0
        for name in data.files:
            arr = data[name]
            total += arr.nbytes
            print(f"[存档] {name}: shape={arr.shape} dtype={arr.dtype}")
    print(f"[存档] 浮点权重共 {total / 1024:.1f} KB,int8 量化后预计 {total / 4 / 1024:.1f} KB")


def main() -> None:
    weights = make_weights()
    export_weights(weights)
    inspect_archive()
    q = quantize_model(weights)
    for name in weights:
        err = float(np.max(np.abs(weights[name] - dequantize(q[name + "_q"], q[name + "_scale"]))))
        print(f"[误差] {name}: 反量化最大误差={err:.4f}")


if __name__ == "__main__":
    main()
