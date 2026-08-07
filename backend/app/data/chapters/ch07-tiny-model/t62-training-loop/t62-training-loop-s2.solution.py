"""t62 训练循环与优化 · s2:训练循环与梯度下降。"""
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
    steps, lr = 60, 1.0
    his = []
    for s in range(steps):
        grads = numerical_grad(model, xtr, ytr)
        update(model, grads, lr)
        his.append(cross_entropy(model, xtr, ytr))
    print(f"训练损失 {his[0]:.4f} → {his[-1]:.4f}")
    plot_curve(his)


if __name__ == "__main__":
    main()
