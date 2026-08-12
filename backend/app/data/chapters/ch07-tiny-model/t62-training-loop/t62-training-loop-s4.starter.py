"""t62 训练循环与优化 · s4:梯度裁剪。"""


# === 学习契约（面向学生）===
# 本节目标：梯度裁剪:防住梯度爆炸。完成后能把本节概念放入可运行的工程链路。
# 需要补写：clip_grads；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `cross_entropy(model, x, y) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `make_data(vocab=16, n=160) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `split_data(x, y, ratio=0.8) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `numerical_grad(model, x, y, h=0.0001) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `update(model, grads, lr) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `lr_warmup_cosine(step, total, warmup, peak) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `clip_grads(grads, max_norm=0.3) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `plot_curve(history) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：按本节调用链完成对应处理
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `MiniGPT`：承载本节状态/数据；重点方法：forward。
# 所属技术栈/模块：模型基础：Tokenizer、numpy、PyTorch、Transformer、训练/微调/量化。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import numpy as np


class MiniGPT:
    def __init__(self, vocab=16, dim=8, seq=8, hid=8, seed=7, scale=0.2):
        rng = np.random.default_rng(seed)
        names = ["wte", "wpe", "wq", "wk", "wv", "wo", "w1", "w2", "wout"]
        shapes = [(vocab, dim), (seq, dim), (dim, dim), (dim, dim), (dim, dim), (dim, dim), (dim, hid), (hid, dim), (dim, vocab)]
        self.params = {n: rng.normal(0, scale, s) for n, s in zip(names, shapes)}
        for n, s in zip(["b1", "b2", "bout"], [(hid,), (dim,), (vocab,)]):
            self.params[n] = np.zeros(s)

    def forward(self, x):
        B, T = x.shape
        dim = self.params["wte"].shape[1]
        h = self.params["wte"][x] + self.params["wpe"][:T]
        q = h @ self.params["wq"]
        k = h @ self.params["wk"]
        v = h @ self.params["wv"]
        sc = q @ k.transpose(0, 2, 1) / np.sqrt(dim)
        mask = np.tril(np.ones((T, T)))[None]
        sc = np.where(mask, sc, -1e9)
        att = np.exp(sc - sc.max(axis=-1, keepdims=True))
        att = att / att.sum(axis=-1, keepdims=True)
        h = h + (att @ v) @ self.params["wo"]
        hh = np.maximum(0.0, h @ self.params["w1"] + self.params["b1"])
        h = h + hh @ self.params["w2"] + self.params["b2"]
        return h @ self.params["wout"] + self.params["bout"]


def cross_entropy(model, x, y):
    logits = model.forward(x)
    B, T, V = logits.shape
    p = np.exp(logits - logits.max(axis=-1, keepdims=True))
    p = p / p.sum(axis=-1, keepdims=True)
    p_y = p.reshape(-1, V)[np.arange(B * T), y.reshape(-1)]
    return float(-np.log(p_y + 1e-9).mean())


def make_data(vocab=16, n=160):
    x = np.arange(n) % vocab
    y = (x + 1) % vocab
    return x.reshape(-1, 8), y.reshape(-1, 8)


def split_data(x, y, ratio=0.8):
    cut = int(len(x) * ratio)
    return x[:cut], y[:cut], x[cut:], y[cut:]


def numerical_grad(model, x, y, h=1e-4):
    grads = {}
    for name, w in model.params.items():
        g = np.zeros_like(w)
        for idx in np.ndindex(w.shape):
            w[idx] += h
            l1 = cross_entropy(model, x, y)
            w[idx] -= 2 * h
            g[idx] = (l1 - cross_entropy(model, x, y)) / (2 * h)
            w[idx] += h
        grads[name] = g
    return grads


def update(model, grads, lr):
    for name, w in model.params.items():
        w -= lr * grads[name]


def lr_warmup_cosine(step, total, warmup, peak):
    if step < warmup:
        return peak * (step + 1) / warmup
    p = (step - warmup) / max(1, total - warmup)
    return peak * 0.5 * (1.0 + np.cos(np.pi * p))


def clip_grads(grads, max_norm=0.3):
    # TODO: 计算全部梯度的总范数 total;若 total > max_norm,按比例缩放所有梯度并返回 total
    # 提示: total = np.sqrt(sum(float((g * g).sum()) for g in grads.values()));if total > max_norm: scale = max_norm / (total + 1e-12);for g in grads.values(): g *= scale;return total
    raise NotImplementedError("t62-training-loop-s4 尚未实现:请按 TODO 提示实现梯度裁剪")


def plot_curve(history):
    cols, rows = 36, 8
    lo, hi = min(history), max(history)
    span = max(hi - lo, 1e-9)
    idx = [int(round(i * (len(history) - 1) / (cols - 1))) for i in range(cols)]
    vals = [history[i] for i in idx]
    for r in range(rows, 0, -1):
        level = lo + span * (r - 1) / rows
        line = "".join("█" if v >= level else " " for v in vals)
        print(f"{level:7.3f} |{line}|")
    print(f"起始 {history[0]:.3f} → 结束 {history[-1]:.3f}(共 {len(history)} 个点)")


def main() -> None:
    model = MiniGPT()
    x, y = make_data()
    xtr, ytr, xva, yva = split_data(x, y)
    steps, peak, warmup, max_norm = 60, 1.0, 5, 0.3
    his, norms, n_clip = [], [], 0
    for s in range(steps):
        lr = lr_warmup_cosine(s, steps, warmup, peak)
        grads = numerical_grad(model, xtr, ytr)
        # TODO: raw = clip_grads(grads, max_norm) 获取裁剪前范数
        # 提示: raw = clip_grads(grads, max_norm)
        raise NotImplementedError("t62-training-loop-s4 尚未实现:请按 TODO 提示调用 clip_grads 并记录裁剪前范数")
        norms.append(raw)
        n_clip += int(raw > max_norm)
        update(model, grads, lr)
        his.append(cross_entropy(model, xtr, ytr))
    print(f"裁剪前梯度范数:max {max(norms):.3f},mean {sum(norms) / len(norms):.3f}")
    print(f"裁剪次数: {n_clip}/{steps}")
    print(f"训练损失 {his[0]:.4f} → {his[-1]:.4f}")
    plot_curve(his)


if __name__ == "__main__":
    main()
