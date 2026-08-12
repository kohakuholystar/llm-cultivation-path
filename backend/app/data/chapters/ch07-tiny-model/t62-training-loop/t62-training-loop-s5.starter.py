"""t62 · PyTorch 训练与 checkpoint：从 NumPy 原理走向真实制品。

这个练习使用一个很小的字符预测任务来验证训练、保存和加载的流程。
它不是预训练语言模型，也不承诺生成质量；这里的可交付物是可复现的
PyTorch checkpoint，而不是随机初始化后假称的“训练产物”。
"""


# === 学习契约（面向学生）===
# 本节目标：PyTorch checkpoint：训练、保存与可验证恢复。完成后能把本节概念放入可运行的工程链路。
# 需要补写：step；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `make_batch() -> tuple[torch.Tensor, torch.Tensor]`：输入为签名中的参数；输出为 `tuple[torch.Tensor, torch.Tensor]`。用途：固定、可复现的映射：0→1、1→2，…，7→0。
#   - `train_one_epoch(model: TinyNextTokenModel, inputs: torch.Tensor, targets: torch.Tensor, optimizer: torch.optim.Optimizer, loss_fn: nn.Module) -> float`：输入为签名中的参数；输出为 `float`。用途：按本节调用链完成对应处理
#   - `save_checkpoint(model: TinyNextTokenModel, path: Path) -> None`：输入为签名中的参数；输出为 `None`。用途：保存权重和重建模型必需的配置；不要保存 API Key 或任意用户数据。
#   - `load_checkpoint(path: Path) -> TinyNextTokenModel`：输入为签名中的参数；输出为 `TinyNextTokenModel`。用途：按本节调用链完成对应处理
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `TinyNextTokenModel`：承载本节状态/数据；重点方法：forward。
# 所属技术栈/模块：模型基础：Tokenizer、numpy、PyTorch、Transformer、训练/微调/量化。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。 本节还需要 ML 沙箱依赖（如 PyTorch/Transformers）。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
from pathlib import Path

import torch
from torch import nn


VOCAB_SIZE = 8
HIDDEN_SIZE = 16
ARTIFACT_PATH = Path("/workspace/tiny_next_token.pt")


class TinyNextTokenModel(nn.Module):
    """极小的下一 token 预测器：Embedding 后接线性分类器。"""

    def __init__(self, vocab_size: int = VOCAB_SIZE, hidden_size: int = HIDDEN_SIZE) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.classifier = nn.Linear(hidden_size, vocab_size)

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.embedding(token_ids))


def make_batch() -> tuple[torch.Tensor, torch.Tensor]:
    """固定、可复现的映射：0→1、1→2，…，7→0。"""
    inputs = torch.arange(VOCAB_SIZE, dtype=torch.long).repeat(16)
    targets = (inputs + 1) % VOCAB_SIZE
    return inputs, targets


def train_one_epoch(
    model: TinyNextTokenModel,
    inputs: torch.Tensor,
    targets: torch.Tensor,
    optimizer: torch.optim.Optimizer,
    loss_fn: nn.Module,
) -> float:
    # TODO: 按“清梯度 → 前向 → loss → backward → optimizer.step()”完成一次真实更新。
    # 提示：optimizer.zero_grad(); logits = model(inputs); loss = loss_fn(logits, targets)
    #       loss.backward(); optimizer.step(); return float(loss.item())
    raise NotImplementedError("请完成一次 PyTorch 训练更新")


def save_checkpoint(model: TinyNextTokenModel, path: Path) -> None:
    """保存权重和重建模型必需的配置；不要保存 API Key 或任意用户数据。"""
    torch.save(
        {
            "format": "tiny-next-token-v1",
            "vocab_size": VOCAB_SIZE,
            "hidden_size": HIDDEN_SIZE,
            "model_state": model.state_dict(),
        },
        path,
    )


def load_checkpoint(path: Path) -> TinyNextTokenModel:
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if payload.get("format") != "tiny-next-token-v1":
        raise ValueError("不是本课程生成的 checkpoint")
    restored = TinyNextTokenModel(payload["vocab_size"], payload["hidden_size"])
    restored.load_state_dict(payload["model_state"])
    restored.eval()
    return restored


def main() -> None:
    torch.manual_seed(7)
    model = TinyNextTokenModel()
    inputs, targets = make_batch()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.08)
    loss_fn = nn.CrossEntropyLoss()
    losses = [train_one_epoch(model, inputs, targets, optimizer, loss_fn) for _ in range(40)]

    model.eval()
    with torch.no_grad():
        before = model(inputs)
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_checkpoint(model, ARTIFACT_PATH)
    restored = load_checkpoint(ARTIFACT_PATH)
    with torch.no_grad():
        after = restored(inputs)

    identical = torch.equal(before, after)
    print(f"训练损失 {losses[0]:.4f} → {losses[-1]:.4f}")
    print(f"checkpoint 行为校验:{'通过' if identical else '失败'}")
    print(f"制品路径: {ARTIFACT_PATH.name},参数张量数: {len(model.state_dict())}")


if __name__ == "__main__":
    main()
