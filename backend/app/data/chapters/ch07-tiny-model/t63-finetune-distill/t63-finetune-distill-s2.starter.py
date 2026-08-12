"""模型研究小组 · s2:冻结主干——LoRALayer 入处理器

LoRA 不直接改写预训练权重:它把 W 冻结,在旁边挂一条
「低秩旁路」ΔW = alpha/r · A@B。微调时只动 A、B,
主干一行不改——参数高效微调的秘密就在这。
"""


# === 学习契约（面向学生）===
# 本节目标：冻结主干:LoRALayer 入处理器。完成后能把本节概念放入可运行的工程链路。
# 需要补写：delta；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `LoRALayer`：承载本节状态/数据；重点方法：delta, forward, trainable_params, frozen_params, summary。
# 所属技术栈/模块：模型基础：Tokenizer、numpy、PyTorch、Transformer、训练/微调/量化。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
        # TODO: 初始化三个权重与缩放系数:
        #   self.scale = alpha / r                    缩放系数
        #   self.w     = rng.normal(0.0, 0.3, (d, d)) 冻结主干
        #   self.a     = rng.normal(0.0, 0.05, (d, r))可训练左因子
        #   self.b     = np.zeros((r, d))             可训练右因子(零初始化)
        pass

    def delta(self) -> np.ndarray:
        """低秩增量矩阵:scale * A@B。"""
        return self.scale * (self.a @ self.b)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """输出 = x@W + x@delta(B 为零时与冻结主干一致)。"""
        # TODO: 返回 x @ (self.w + self.delta())
        pass

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
    print("== 冻结主干:LoRALayer 入处理器 ==")
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
