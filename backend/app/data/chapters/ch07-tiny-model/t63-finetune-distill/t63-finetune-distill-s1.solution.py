"""袖里乾坤 · s1:低秩分解——LoRA 的数学雏形

预训练权重矩阵往往「外强中干」:看似上千个参数,能量却
集中在少数几个方向上。低秩分解(即 SVD 截断)用两个瘦长
小矩阵的乘积近似原矩阵——这正是 LoRA「用低秩旁路替代
大矩阵更新量」的数学源头。本步先把 SVD 这个雏形做出来。
"""
import numpy as np

V = 35  # 模拟大模型的单层隐藏维度
NOISE = 0.02  # 权重里的细微噪声


def make_structured_weight(seed: int = 42) -> np.ndarray:
    """构造一个「有结构」的权重:6 个主方向 + 微噪声。"""
    rng = np.random.default_rng(seed)
    u = rng.normal(0.0, 1.0, size=(V, 6))
    vt = rng.normal(0.0, 1.0, size=(6, V))
    s = np.array([3.0, 2.0, 1.5, 1.0, 0.5, 0.25])
    # 主方向按奇异值权重叠加,再混入微噪声
    return u @ (s[:, None] * vt) + NOISE * rng.normal(0.0, 1.0, size=(V, V))


def low_rank_factorize(w: np.ndarray, r: int):
    """把 w 分解为 A@B ≈ w,返回 (A, B)。

    SVD 截断:只保留前 r 个奇异值。u[:, :r]*s[:r] 与
    vt[:r, :] 分别就是两个瘦长因子 A 与 B。
    """
    u, s, vt = np.linalg.svd(w, full_matrices=False)
    a = u[:, :r] * s[:r]
    b = vt[:r, :]
    return a, b


def reconstruction_error(w, a, b) -> float:
    """相对重建误差:||W - A@B||_F / ||W||_F。"""
    return float(np.linalg.norm(w - a @ b) / np.linalg.norm(w))


def singular_spectrum(w) -> np.ndarray:
    """返回 w 的奇异值谱(降序排列)。"""
    return np.linalg.svd(w, compute_uv=False)


def main() -> None:
    print("== 低秩分解:LoRA 的数学雏形 ==")
    w = make_structured_weight()
    sv = singular_spectrum(w)
    print(f"权重形状 {w.shape},参数 {w.size}")
    print("前 8 个奇异值:", np.round(sv[:8], 3))
    print("→ 前 6 个远大于其余,能量集中在主方向上")

    # 扫描不同秩:误差、参数量、压缩率三者联动
    print("\n截断秩 r | 相对重建误差 | 分解参数 | 压缩率")
    for r in (2, 4, 6):
        a, b = low_rank_factorize(w, r)
        err = reconstruction_error(w, a, b)
        n_low = a.size + b.size
        print(f"  {r} | {err:.4f} | {n_low} | {w.size / n_low:.2f}x")

    # 秩越大误差越小;r=6 时已逼近噪声下限(0.02 量级)
    a, b = low_rank_factorize(w, 4)
    print(f"\n秩 4 分解:W {w.shape} → A {a.shape}、B {b.shape}")
    print(f"参数 {w.size} → {a.size + b.size},"
          f"只剩 {100 * (a.size + b.size) / w.size:.0f}%")
    print("重建后的权重仍能还原主体结构——这就是低秩的精髓")


if __name__ == "__main__":
    main()
