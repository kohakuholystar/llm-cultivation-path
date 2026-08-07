"""袖里乾坤 · s2:冻结主干——LoRALayer 入炉

LoRA 不直接改写预训练权重:它把 W 冻结,在旁边挂一条
「低秩旁路」ΔW = alpha/r · A@B。微调时只动 A、B,
主干一行不改——参数高效微调的秘密就在这。
"""
import numpy as np

V = 35
ALPHA = 4.0
RANK = 4


class LoRALayer:
    """一个带低秩旁路的线性层:w 冻结,A/B 可训练。"""

    def __init__(self, d: int, r: int, alpha: float, seed: int = 7):
        rng = np.random.default_rng(seed)
        self.d = d
        self.r = r
        self.scale = alpha / r  # 缩放系数:alpha 是超参,r 是秩
        self.w = rng.normal(0.0, 0.3, size=(d, d))  # 冻结:预训练主干
        self.a = rng.normal(0.0, 0.05, size=(d, r))  # 可训练:旁路左因子
        self.b = np.zeros((r, d))  # 可训练:旁路右因子,零初始化
        # B 全零 ⇒ ΔW 初始为 0,微调前后模型行为不突变

    def delta(self) -> np.ndarray:
        """低秩增量矩阵:scale * A@B。"""
        return self.scale * (self.a @ self.b)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """输出 = x@W + x@delta(B 为零时与冻结主干一致)。"""
        return x @ (self.w + self.delta())

    def trainable_params(self) -> int:
        """旁路 A、B 的参数总数。"""
        return self.a.size + self.b.size

    def frozen_params(self) -> int:
        """冻结主干的参数总数。"""
        return self.w.size

    def summary(self) -> str:
        return (f"d={self.d}, r={self.r}, scale={self.scale:.3f}: "
                f"可训练 {self.trainable_params()} / 冻结 {self.frozen_params()}")


def main() -> None:
    print("== 冻结主干:LoRALayer 入炉 ==")
    layer = LoRALayer(V, RANK, ALPHA)
    print(layer.summary())
    total = layer.trainable_params() + layer.frozen_params()
    print(f"可训练参数占比:{100 * layer.trainable_params() / total:.2f}%")

    x = np.eye(V)[[0, 1, 2]]  # 取 3 个 one-hot 输入
    base = x @ layer.w
    out = layer.forward(x)
    print(f"初始旁路为零,forward 与主干一致: {np.allclose(base, out)}")

    # 手动扰动 B,让旁路开始起作用
    layer.b += 0.01
    diff = np.max(np.abs(layer.forward(x) - base))
    print(f"扰动 B 后 ΔW 秩 = {np.linalg.matrix_rank(layer.delta())}")
    print(f"扰动 B 后输出差最大值 = {diff:.5f}")
    print("微调阶段只更新 A/B,主干 w 永不进入梯度更新")


if __name__ == "__main__":
    main()
