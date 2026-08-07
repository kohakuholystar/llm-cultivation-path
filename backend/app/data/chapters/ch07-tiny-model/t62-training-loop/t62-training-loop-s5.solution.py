"""t62 训练循环与优化 · s5:checkpoint 保存与恢复。"""
import json

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
    total = np.sqrt(sum(float((g * g).sum()) for g in grads.values()))
    if total > max_norm:
        scale = max_norm / (total + 1e-12)
        for g in grads.values():
            g *= scale
    return total


def save_checkpoint(model, path):
    payload = {name: w.tolist() for name, w in model.params.items()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def load_checkpoint(model, path):
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    for name, arr in payload.items():
        model.params[name] = np.array(arr)


def main() -> None:
    model = MiniGPT()
    x, y = make_data()
    xtr, ytr, xva, yva = split_data(x, y)
    steps, peak, warmup, max_norm = 60, 1.0, 5, 0.3
    his, n_clip = [], 0
    for s in range(steps):
        lr = lr_warmup_cosine(s, steps, warmup, peak)
        grads = numerical_grad(model, xtr, ytr)
        n_clip += int(clip_grads(grads, max_norm) > max_norm)
        update(model, grads, lr)
        his.append(cross_entropy(model, xtr, ytr))
    print(f"裁剪次数: {n_clip}/{steps}")
    print(f"训练损失 {his[0]:.4f} → {his[-1]:.4f}")
    path = "mini_gpt_ckpt.json"
    save_checkpoint(model, path)
    fresh = MiniGPT()
    load_checkpoint(fresh, path)
    ok = abs(cross_entropy(model, xva, yva) - cross_entropy(fresh, xva, yva)) < 1e-9
    print(f"checkpoint 校验:{'通过' if ok else '失败'}")
    print(f"存档路径: {path},参数组数: {len(model.params)}")


if __name__ == "__main__":
    main()
