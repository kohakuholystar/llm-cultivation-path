"""模型研究小组 · s1:低秩分解——LoRA 的数学雏形

预训练权重矩阵往往「外强中干」:看似上千个参数,能量却
集中在少数几个方向上。低秩分解(即 SVD 截断)用两个瘦长
小矩阵的乘积近似原矩阵——这正是 LoRA「用低秩旁路替代
大矩阵更新量」的数学源头。本步先把 SVD 这个雏形做出来。
"""


# === 学习契约（面向学生）===
# 本节目标：低秩分解:LoRA 的数学雏形。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `make_structured_weight(seed: int=42) -> np.ndarray`：输入为签名中的参数；输出为 `np.ndarray`。用途：构造一个「有结构」的权重:6 个主方向 + 微噪声。
#   - `low_rank_factorize(w: np.ndarray, r: int) -> 未标注`：输入为签名中的参数；输出为 `函数约定的返回值或状态更新`。用途：把 w 分解为 A@B ≈ w,返回 (A, B)。
#   - `reconstruction_error(w, a, b) -> float`：输入为签名中的参数；输出为 `float`。用途：相对重建误差:||W - A@B||_F / ||W||_F。
#   - `singular_spectrum(w) -> np.ndarray`：输入为签名中的参数；输出为 `np.ndarray`。用途：返回 w 的奇异值谱(降序排列)。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：模型基础：Tokenizer、numpy、PyTorch、Transformer、训练/微调/量化。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
    # TODO: 对 w 做 SVD 截断,只保留前 r 个奇异值,返回瘦长因子 (A, B)
    # 提示: u, s, vt = np.linalg.svd(w, full_matrices=False);
    #       A 取 u 的前 r 列并按 s[:r] 缩放,B 取 vt 的前 r 行
    raise NotImplementedError("low_rank_factorize 尚未实现:请按 TODO 提示完成 SVD 截断")


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
    # TODO: 对 r 依次取 (2, 4, 6),计算重建误差、分解参数与压缩率并打印表格行
    # 提示: for r in (2, 4, 6): 内调用 low_rank_factorize 得 (a, b);
    #       err = reconstruction_error(w, a, b);n_low = a.size + b.size;
    #       打印 f"  {r} | {err:.4f} | {n_low} | {w.size / n_low:.2f}x"
    raise NotImplementedError("main 尚未实现:请按 TODO 提示完成截断秩扫描表格")

    # 秩越大误差越小;r=6 时已逼近噪声下限(0.02 量级)
    a, b = low_rank_factorize(w, 4)
    print(f"\n秩 4 分解:W {w.shape} → A {a.shape}、B {b.shape}")
    print(f"参数 {w.size} → {a.size + b.size},"
          f"只剩 {100 * (a.size + b.size) / w.size:.0f}%")
    print("重建后的权重仍能还原主体结构——这就是低秩的精髓")


if __name__ == "__main__":
    main()
