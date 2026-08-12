"""模型研究小组 · s4:只训旁路——LoRA 微调循环

LoRALayer 与交叉熵已备齐。现在手动写 SGD:每一轮只按
梯度更新 A、B 两个旁路因子,冻结的主干 w 全程不动。
训练结束校验 w 与开始前逐元素相同——「参数高效」这四个字,
是用校验证明出来的。
"""


# === 学习契约（面向学生）===
# 本节目标：只训旁路:LoRA 微调循环。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `build_bigram_data(ids) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：构造 bigram 数据:输入前一字,预测后一字。
#   - `to_onehot(xs, vocab: int) -> np.ndarray`：输入为签名中的参数；输出为 `np.ndarray`。用途：编号 → one-hot 矩阵(每行一个样本)。
#   - `softmax(z) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按行 softmax,先减行最大值防止溢出。
#   - `cross_entropy_with_grad(logits, ys) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：交叉熵损失与其对 logits 的梯度。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `LoRALayer`：承载本节状态/数据；重点方法：delta, forward, trainable_params。
# 所属技术栈/模块：模型基础：Tokenizer、numpy、PyTorch、Transformer、训练/微调/量化。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import numpy as np

CORPUS = ("社团展台调灯光,参数三轮见成效。"
          "丹青入册黑糖资料室,阁中坐忘修心性。"
          "心性圆融通完整路线,完整路线无形育众生。")
chars = sorted(set(CORPUS))
VOCAB = len(chars)
CHAR_IDS = {c: i for i, c in enumerate(chars)}
IDS = np.array([CHAR_IDS[c] for c in CORPUS], dtype=np.int64)

EPOCHS = 1500
LR = 0.5
RANK = 4
ALPHA = 4.0
SEED = 7


def build_bigram_data(ids):
    """构造 bigram 数据:输入前一字,预测后一字。"""
    return ids[:-1], ids[1:]


def to_onehot(xs, vocab: int) -> np.ndarray:
    """编号 → one-hot 矩阵(每行一个样本)。"""
    x = np.zeros((len(xs), vocab), dtype=np.float64)
    x[np.arange(len(xs)), xs] = 1.0
    return x


def softmax(z):
    """按行 softmax,先减行最大值防止溢出。"""
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def cross_entropy_with_grad(logits, ys):
    """交叉熵损失与其对 logits 的梯度。"""
    # TODO: 用 softmax 算 p,取样本数 n;
    #   loss = -np.mean(np.log(p[np.arange(n), ys] + 1e-12));
    #   d = (p - np.eye(logits.shape[1])[ys]) / n;返回 (loss, d)
    pass


class LoRALayer:
    """带低秩旁路的线性层:w 冻结,A/B 可训练。"""

    def __init__(self, d: int, r: int, alpha: float, seed: int):
        rng = np.random.default_rng(seed)
        self.d = d
        self.r = r
        self.scale = alpha / r
        self.w = rng.normal(0.0, 0.3, size=(d, d))
        self.a = rng.normal(0.0, 0.05, size=(d, r))
        self.b = np.zeros((r, d))

    def delta(self) -> np.ndarray:
        """低秩增量矩阵:scale * A@B。"""
        return self.scale * (self.a @ self.b)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """输出 = x@W + x@delta。"""
        return x @ (self.w + self.delta())

    def trainable_params(self) -> int:
        return self.a.size + self.b.size


def main() -> None:
    print("== 只训旁路:LoRA 微调循环 ==")
    xs, ys = build_bigram_data(IDS)
    x = to_onehot(xs, VOCAB)

    model = LoRALayer(VOCAB, RANK, ALPHA, SEED)
    w_before = model.w.copy()  # 备份冻结主干,留作训练后校验
    loss0, _ = cross_entropy_with_grad(model.forward(x), ys)
    print(f"初始 loss = {loss0:.4f} | 可训练参数 = {model.trainable_params()}")

    for epoch in range(1, EPOCHS + 1):
        logits = model.forward(x)
        loss, dlogits = cross_entropy_with_grad(logits, ys)
        # TODO: 链式法则求旁路梯度:
        #   dw = x.T @ dlogits                      对 W_eff 的梯度
        #   da = model.scale * (dw @ model.b.T)     对 A 的梯度
        #   db = model.scale * (model.a.T @ dw)     对 B 的梯度
        #   然后 model.a -= LR * da;model.b -= LR * db
        pass
        if epoch % 300 == 0:
            print(f"  epoch {epoch:5d} | loss {loss:.4f}")

    frozen_ok = np.array_equal(model.w, w_before)
    print(f"\n训练结束 | loss {loss0:.4f} → {loss:.4f}")
    print(f"冻结校验:主干 w 与训练前逐元素相同 = {frozen_ok}")
    assert frozen_ok, "冻结主干被意外修改!"
    print(f"旁路 ΔW 秩 = {np.linalg.matrix_rank(model.delta())}")
    print("只训旁路完成:冻结主干,参数高效微调")


if __name__ == "__main__":
    main()
