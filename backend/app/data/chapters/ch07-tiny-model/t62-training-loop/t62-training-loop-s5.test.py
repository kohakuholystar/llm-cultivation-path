"""权威行为测试：在 ml 镜像中验证真实 PyTorch 制品链。"""
import importlib.util
from pathlib import Path

import pytest


if importlib.util.find_spec("torch") is None:
    pytest.skip("此步骤需要 ml 沙箱镜像中的 PyTorch", allow_module_level=True)


spec = importlib.util.spec_from_file_location("student", "student_submission.py")
student = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(student)


def test_training_reduces_loss_and_saved_model_restores_identical_logits(tmp_path: Path) -> None:
    torch = student.torch
    torch.manual_seed(7)
    model = student.TinyNextTokenModel()
    inputs, targets = student.make_batch()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.08)
    loss_fn = student.nn.CrossEntropyLoss()
    first = student.train_one_epoch(model, inputs, targets, optimizer, loss_fn)
    for _ in range(20):
        final = student.train_one_epoch(model, inputs, targets, optimizer, loss_fn)
    assert final < first

    path = tmp_path / "tiny_next_token.pt"
    model.eval()
    with torch.no_grad():
        expected = model(inputs)
    student.save_checkpoint(model, path)
    restored = student.load_checkpoint(path)
    with torch.no_grad():
        actual = restored(inputs)
    assert torch.equal(expected, actual)
