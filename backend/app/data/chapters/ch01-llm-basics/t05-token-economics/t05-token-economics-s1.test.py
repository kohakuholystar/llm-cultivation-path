"""Behaviour checks for t05-s1.

Student code is made available to this trusted test as ``student_submission``
by the server-owned validation runner.
"""
from student_submission import CHAT_OVERHEAD, TokenMeter


def test_count_text_uses_the_configured_encoding() -> None:
    meter = TokenMeter()
    text = "星澈助手 token 计数"
    assert meter.count_text(text) == len(meter.encoding.encode(text))


def test_count_messages_adds_every_message_overhead() -> None:
    meter = TokenMeter()
    messages = [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "你好"},
    ]
    expected = sum(CHAT_OVERHEAD + meter.count_text(item["content"]) for item in messages)
    assert meter.count_messages(messages) == expected
