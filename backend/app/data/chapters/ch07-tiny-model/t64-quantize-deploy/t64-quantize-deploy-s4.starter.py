"""袖里乾坤 · s4:模型打包

把训练产物变成「开箱即用」的单一交付物:量化权重压进 .npz,
词表与配置写进 manifest.json,再写 load_model 读回并自检
(张量齐全、类型正确、scale 为正),为 s5 的推理服务备好食粮。
"""
import json
import os

import numpy as np

np.random.seed(42)

VOCAB = list("abcdefghijklmnopqrstuvwxyz ")
V, H = len(VOCAB), 16
CONFIG = {"vocab": V, "hidden": H}
PACK_NPZ = "tiny_quant.npz"
PACK_JSON = "manifest.json"


def make_weights() -> dict:
    """蒸馏产物权重:嵌入/隐藏/输出三矩阵,演示用随机权重。"""
    rand = lambda *s: np.random.randn(*s).astype(np.float32) * 0.1
    return {"embed": rand(V, H), "hidden": rand(H, H), "out": rand(H, V)}


def quantize_tensor(w: np.ndarray) -> tuple:
    """对称 int8 量化:返回 (int8 权重, scale)。"""
    scale = float(np.max(np.abs(w))) / 127.0
    return np.round(w / scale).astype(np.int8), scale


def quantize_model(weights: dict) -> dict:
    """逐张量量化,键名加上 _q / _scale 后缀。"""
    out = {}
    for name, w in weights.items():
        qw, scale = quantize_tensor(w)
        out[name + "_q"] = qw
        out[name + "_scale"] = scale
    return out


def save_model(qw: dict, path: str = PACK_NPZ) -> dict:
    """打包:量化张量写 .npz,词表与配置写 manifest.json,返回清单。"""
    np.savez_compressed(path, **qw)
    manifest = {
        "name": "weikun-tiny-gpt",
        "format": "int8-symmetric",
        "config": CONFIG,
        "vocab": VOCAB,
        "tensors": sorted(n for n in qw if n.endswith("_q")),
        "scales": {n: float(qw[n]) for n in qw if n.endswith("_scale")},
    }
    with open(PACK_JSON, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest


def load_model(path: str = PACK_NPZ) -> dict:
    """读回打包产物并自检:张量齐全、int8 类型、scale 为正。"""
    with open(PACK_JSON, encoding="utf-8") as f:
        manifest = json.load(f)
    with np.load(path) as data:
        qw = {name: data[name] for name in data.files}
    # TODO: 按 manifest 的三份契约校验打包产物,不满足直接 raise ValueError
    # 提示: 遍历 manifest["tensors"]:先查 name in qw,再查 qw[name].dtype == np.int8;
    #       遍历 manifest["scales"]:检查每个 scale > 0;全部通过后 return qw
    raise NotImplementedError("load_model 尚未实现:请按 TODO 提示完成三份契约校验")
    return qw


def main() -> None:
    q = quantize_model(make_weights())
    manifest = save_model(q)
    print(f"[打包] 已写出 {PACK_NPZ}({os.path.getsize(PACK_NPZ)} 字节)与 {PACK_JSON}")
    print(f"[打包] 模型名 {manifest['name']},量化格式 {manifest['format']}")
    qw = load_model()
    for name in manifest["tensors"]:
        arr = qw[name]
        print(f"[校验] {name}: shape={arr.shape} dtype={arr.dtype} ✓")
    print("[加载] 模型恢复成功,可交付出推理服务使用")


if __name__ == "__main__":
    main()
