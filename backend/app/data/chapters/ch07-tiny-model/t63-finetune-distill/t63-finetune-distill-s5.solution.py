"""模型研究小组 · s5:师徒传承——知识蒸馏与软标签

教师全参微调,学生 LoRA 学旁路:甲看硬标签,乙偷师教师的
软分布 softmax(logits/T),软标签藏着同义字、近邻字的暗知识。
"""
import numpy as np

CORPUS = ("社团展台调灯光,参数三轮见成效。"
          "丹青入册黑糖资料室,阁中坐忘修心性。"
          "心性圆融通完整路线,完整路线无形育众生。")
chars = sorted(set(CORPUS))
VOCAB = len(chars)
CHAR_IDS = {c: i for i, c in enumerate(chars)}
IDS = np.array([CHAR_IDS[c] for c in CORPUS], dtype=np.int64)

TEACHER_EPOCHS = 600
TEACHER_LR = 0.15
STUDENT_EPOCHS = 500
STUDENT_LR = 0.5
RANK = 2
ALPHA = 4.0
TEMP = 4.0
SEED = 21


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


def soft_kl(pa, pt, eps: float = 1e-12) -> float:
    """KL(pa || pt),对样本求平均。"""
    return float(np.mean(np.sum(pa * (np.log(pa + eps) - np.log(pt + eps)), axis=1)))


def distill_grad(student_logits, teacher_logits, t: float):
    """软标签目标下的损失与梯度。

    温度 t 把两个分布都摊软,再算 KL;损失乘 t² 保证
    梯度量级与硬标签训练可比,梯度 = t*(ps - pt)/n。
    """
    ps = softmax(student_logits / t)
    pt = softmax(teacher_logits / t)
    n = student_logits.shape[0]
    loss = t * t * soft_kl(ps, pt)
    d = t * (ps - pt) / n
    return loss, d


def train_teacher(w, x, ys, epochs: int, lr: float):
    """教师:全参数 SGD,更新全部权重。"""
    for _ in range(epochs):
        _, dlogits = cross_entropy_with_grad(x @ w, ys)
        w -= lr * (x.T @ dlogits)
    return w


def train_student(model, x, ys, teacher_logits, epochs: int, lr: float, t: float):
    """学生:只更新旁路。teacher_logits 为 None 时用硬标签,否则用软标签。"""
    for _ in range(epochs):
        logits = model.forward(x)
        if teacher_logits is None:
            _, dlogits = cross_entropy_with_grad(logits, ys)
        else:
            _, dlogits = distill_grad(logits, teacher_logits, t)
        dw = x.T @ dlogits
        model.a -= lr * model.scale * (dw @ model.b.T)
        model.b -= lr * model.scale * (model.a.T @ dw)
    return model


def main() -> None:
    print("== 师徒传承:知识蒸馏与软标签 ==")
    xs, ys = build_bigram_data(IDS)
    x = to_onehot(xs, VOCAB)

    w_t = np.random.default_rng(42).normal(0.0, 0.3, size=(VOCAB, VOCAB))
    w_t = train_teacher(w_t, x, ys, TEACHER_EPOCHS, TEACHER_LR)
    t_loss, _ = cross_entropy_with_grad(x @ w_t, ys)
    t_logits = x @ w_t
    print(f"教师(全参微调 {TEACHER_EPOCHS} 轮) loss = {t_loss:.4f}")

    student_a = LoRALayer(VOCAB, RANK, ALPHA, SEED)
    student_a = train_student(student_a, x, ys, None, STUDENT_EPOCHS, STUDENT_LR, TEMP)
    pa = softmax(student_a.forward(x))
    kl_a = soft_kl(pa, softmax(t_logits))
    print(f"学生甲(硬标签)与教师 KL 距离 = {kl_a:.4f}")

    student_b = LoRALayer(VOCAB, RANK, ALPHA, SEED)
    student_b = train_student(student_b, x, ys, t_logits, STUDENT_EPOCHS, STUDENT_LR, TEMP)
    pb = softmax(student_b.forward(x))
    kl_b = soft_kl(pb, softmax(t_logits))
    print(f"学生乙(软标签)与教师 KL 距离 = {kl_b:.4f}")

    print(f"蒸馏学生乙更接近教师: {kl_b < kl_a}")


if __name__ == "__main__":
    main()
