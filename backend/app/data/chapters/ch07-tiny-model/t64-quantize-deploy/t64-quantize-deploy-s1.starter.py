"""模型研究小组 · s1:权重落盘与 int8 量化

蒸馏出的小模型(字符级,随机演示权重)先落盘成 .npz,
再实现 int8 对称量化:算 scale、量化、反量化、评估误差。
这是模型从 32 位浮点压缩到四分之一体积的第一步。
"""


# === 学习契约（面向学生）===
# 本节目标：权重落盘:int8 量化初窥门径。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `make_weights() -> dict`：输入为签名中的参数；输出为 `dict`。用途：蒸馏产物权重:嵌入/隐藏/输出三矩阵,演示用随机权重。
#   - `quantize_tensor(w: np.ndarray) -> tuple`：输入为签名中的参数；输出为 `tuple`。用途：对称 int8 量化:返回 (int8 权重, scale)。
#   - `dequantize(q: np.ndarray, scale: float) -> np.ndarray`：输入为签名中的参数；输出为 `np.ndarray`。用途：反量化:把 int8 权重还原成浮点近似。
#   - `quantize_model(weights: dict) -> dict`：输入为签名中的参数；输出为 `dict`。用途：逐张量量化,键名加上 _q / _scale 后缀。
#   - `export_weights(weights: dict) -> None`：输入为签名中的参数；输出为 `None`。用途：把原始浮点权重导出为 .npz 存档。
#   - `inspect_archive() -> None`：输入为签名中的参数；输出为 `None`。用途：读回 .npz,核对张量形状,并预告量化后的体积收益。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：模型基础：Tokenizer、numpy、PyTorch、Transformer、训练/微调/量化。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
    # TODO: 对权重 w 做对称 int8 量化,返回 (int8 权重, scale)
    # 提示: scale 用 np.max(np.abs(w)) / 127.0(记得转 float);
    #       量化 = np.round(w / scale) 后 astype(np.int8)
    raise NotImplementedError("quantize_tensor 尚未实现:请按 TODO 提示完成对称量化")


def dequantize(q: np.ndarray, scale: float) -> np.ndarray:
    """反量化:把 int8 权重还原成浮点近似。"""
    # TODO: 把 int8 权重还原成浮点近似
    # 提示: 乘以量化步长 scale 即可,返回 q * scale
    raise NotImplementedError("dequantize 尚未实现:请按 TODO 提示完成反量化")


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
