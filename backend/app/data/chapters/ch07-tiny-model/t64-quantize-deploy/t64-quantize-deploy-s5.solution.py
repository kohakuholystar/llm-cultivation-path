"""模型研究小组 · s5:简易推理服务

把量化小模型挂上 HTTP:字符级 GPT 吃进 {"prompt": "hello"},
吐出 {"prompt": ..., "generated": "hello..."} 的续写结果,
用一台玩具服务器完成"模型开口说话"的最后一公里。
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen

import numpy as np

np.random.seed(42)

VOCAB = list("abcdefghijklmnopqrstuvwxyz ")
V, H = len(VOCAB), 16
CONFIG = {"vocab": V, "hidden": H}


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


def tokens_of(text: str) -> list[int]:
    """把文本映射成词表下标;词表外的字符一律回退为空格。"""
    return [VOCAB.index(ch) if ch in VOCAB else VOCAB.index(" ") for ch in text]


def dyn_quant(x: np.ndarray) -> tuple:
    """动态量化激活向量:返回 (int8 向量, scale)。"""
    scale = float(np.max(np.abs(x))) / 127.0
    return np.round(x / scale).astype(np.int8), scale


def forward_int8(qw: dict, tokens: list[int]) -> np.ndarray:
    """INT8 整数前向:平均嵌入 → 隐藏层 → 输出 logits。"""
    qe, se = qw["embed_q"], qw["embed_scale"]
    qh, sh = qw["hidden_q"], qw["hidden_scale"]
    qo, so = qw["out_q"], qw["out_scale"]
    x = qe[tokens].astype(np.float32).mean(axis=0) * se
    qx, sx = dyn_quant(x)
    h = qh.astype(np.int32) @ qx.astype(np.int32)
    h = h.astype(np.float32) * (sh * sx)
    qh2, sh2 = dyn_quant(h)
    logits = qh2.astype(np.int32) @ qo.astype(np.int32)
    return logits.astype(np.float32) * (sh2 * so)


def sample_token(logits: np.ndarray) -> int:
    """softmax 概率采样:logits → 下一个字符的词表下标。"""
    e = np.exp(logits - np.max(logits))
    p = e / e.sum()
    return int(np.random.choice(V, p=p))


def generate(qw: dict, prompt: str, max_len: int = 12) -> str:
    """自回归续写:每一步只喂最近 8 个字符,采样一个字符拼上去。"""
    text = prompt
    for _ in range(max_len):
        logits = forward_int8(qw, tokens_of(text[-8:]))
        text += VOCAB[sample_token(logits)]
    return text


class TinyServer(BaseHTTPRequestHandler):
    """玩具推理服务:GET 探活,POST 生成,JSON 进出。"""

    def _json(self, payload: dict) -> bytes:
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def _reply(self, payload: dict) -> None:
        body = self._json(payload)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self._reply({"service": "weikun-tiny-gpt", "status": "ok"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        prompt = str(body.get("prompt", ""))[:8]
        generated = generate(QW, prompt)
        self._reply({"prompt": prompt, "generated": generated})

    def log_message(self, *args) -> None:
        pass  # 静默访问日志,保持终端输出干净


QW = quantize_model(make_weights())


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), TinyServer)
    port = server.server_address[1]

    def call_once() -> None:
        time.sleep(0.3)  # 等服务线程就绪
        req = json.dumps({"prompt": "hello"}).encode("utf-8")
        with urlopen(f"http://127.0.0.1:{port}/", data=req, timeout=5) as resp:
            print(f"[响应] {resp.read().decode('utf-8')}")
        time.sleep(0.2)
        server.shutdown()  # 从另一个线程关闭 serve_forever 循环

    threading.Thread(target=call_once, daemon=True).start()
    print(f"[服务] weikun-tiny-gpt 已启动于 127.0.0.1:{port},处理完请求后自动关闭")
    server.serve_forever()
    print("[关闭] 服务已优雅退出")


if __name__ == "__main__":
    main()
