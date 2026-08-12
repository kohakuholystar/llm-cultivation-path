"""t62 · PyTorch 训练与 checkpoint：从 NumPy 原理走向真实制品。"""
from pathlib import Path

import torch
from torch import nn


VOCAB_SIZE = 8
HIDDEN_SIZE = 16
ARTIFACT_PATH = Path("/workspace/tiny_next_token.pt")


class TinyNextTokenModel(nn.Module):
    def __init__(self, vocab_size: int = VOCAB_SIZE, hidden_size: int = HIDDEN_SIZE) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.classifier = nn.Linear(hidden_size, vocab_size)

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.embedding(token_ids))


def make_batch() -> tuple[torch.Tensor, torch.Tensor]:
    inputs = torch.arange(VOCAB_SIZE, dtype=torch.long).repeat(16)
    targets = (inputs + 1) % VOCAB_SIZE
    return inputs, targets


def train_one_epoch(model, inputs, targets, optimizer, loss_fn) -> float:
    optimizer.zero_grad()
    logits = model(inputs)
    loss = loss_fn(logits, targets)
    loss.backward()
    optimizer.step()
    return float(loss.item())


def save_checkpoint(model: TinyNextTokenModel, path: Path) -> None:
    torch.save({
        "format": "tiny-next-token-v1",
        "vocab_size": VOCAB_SIZE,
        "hidden_size": HIDDEN_SIZE,
        "model_state": model.state_dict(),
    }, path)


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
