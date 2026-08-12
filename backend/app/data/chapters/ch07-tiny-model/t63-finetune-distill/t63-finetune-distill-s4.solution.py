"""模型研究小组 · s4:只训旁路——LoRA 微调循环

LoRALayer 与交叉熵已备齐。现在手动写 SGD:每一轮只按
梯度更新 A、B 两个旁路因子,冻结的主干 w 全程不动。
训练结束校验 w 与开始前逐元素相同——「参数高效」这四个字,
是用校验证明出来的。
"""
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
    p = softmax(logits)
    n = logits.shape[0]
    loss = float(-np.mean(np.log(p[np.arange(n), ys] + 1e-12)))
    d = (p - np.eye(logits.shape[1])[ys]) / n
    return loss, d


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
        # 链式法则:先把对 logits 的梯度传到 W_eff,再沿旁路传
        dw = x.T @ dlogits
        da = model.scale * (dw @ model.b.T)
        db = model.scale * (model.a.T @ dw)
        model.a -= LR * da
        model.b -= LR * db
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
