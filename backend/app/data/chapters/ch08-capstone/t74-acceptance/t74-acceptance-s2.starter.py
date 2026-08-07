"""t74 · s2:记忆与工具分派——对话上下文 + 白名单工具表

集成测试链路已经能跑通,本步给它加上「记忆」与「工具」两块拼图:
ChatMemory 用定长裁剪保留最近对话,dispatch_tool 用白名单查表
分派计算、回显、引用三类工具,未知工具给出友好提示。
"""
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"  # 必须在 import pytest 之前
import pytest

# 用例模板:注入测试文件,由 run_tests 用 pytest 实跑
TEST_CODE = r"""import pytest


def test_load_kb_splits_chunks():
    kb = load_kb("题一\n题二\n\n---\n\n题三\n题四")
    assert kb == ["题一\n题二", "题三\n题四"]


def test_retrieve_scores_by_frequency():
    kb = ["渡劫飞升需要雷劫淬体", "心魔劫最难渡过", "飞升之后成仙"]
    hits = retrieve("渡劫 飞升", kb, top_k=3)
    assert len(hits) == 2
    assert hits[0][0] == "渡劫飞升需要雷劫淬体"
    assert hits[0][1] == 2


def test_format_answer_joins_hits():
    hits = [("渡劫飞升需要雷劫淬体", 2, 0)]
    assert format_answer(hits) == "[1] 渡劫飞升需要雷劫淬体(来源片段 0)"


def test_memory_trims_when_full():
    # TODO: 断言记忆加满后按定长裁剪,只保留最近 max_turns 轮
    # 提示: m = ChatMemory(max_turns=2)
    # 提示: for i in range(6): m.add(f"q{i}", f"a{i}")
    # 提示: assert len(m.history) == 4;assert m.history[0] == ("q2", "a2")
    raise NotImplementedError("t74-acceptance-s2 尚未实现:请按 TODO 提示补全 test_memory_trims_when_full")


def test_memory_recent_returns_tail():
    # TODO: 断言 recent(n) 返回最近 n 轮(2n 条)对话
    # 提示: m = ChatMemory(max_turns=5)
    # 提示: for i in range(6): m.add(f"q{i}", f"a{i}")
    # 提示: tail = m.recent(2);assert len(tail) == 4;assert tail[0] == ("q2", "a2");assert tail[-1] == ("q5", "a5")
    raise NotImplementedError("t74-acceptance-s2 尚未实现:请按 TODO 提示补全 test_memory_recent_returns_tail")


@pytest.mark.parametrize("a,b,op,expect", [(3, 4, "add", 7), (3, 4, "mul", 12), (2, 5, "pow", 32)])
def test_calc_ops(a, b, op, expect):
    # TODO: 断言 calc 工具按 (a, b, op) 查 _CALC 返回结果
    # 提示: assert dispatch_tool("calc", (a, b, op)) == expect
    raise NotImplementedError("t74-acceptance-s2 尚未实现:请按 TODO 提示补全 test_calc_ops")


def test_unknown_tool():
    msg = dispatch_tool("fly", ())
    assert "未知工具" in msg and "calc" in msg


def test_qa_flow():
    kb = ["渡劫需渡雷劫", "飞升需法器"]
    m = ChatMemory()
    m.add("什么是渡劫", format_answer(retrieve("渡劫", kb)))
    assert m.history[-1][0] == "什么是渡劫"
    assert "渡劫需渡雷劫" in m.history[-1][1]
"""


@dataclass
class ChatMemory:
    """定长记忆:只保留最近 max_turns 轮对话,越界自动裁剪。"""

    max_turns: int = 5
    history: list = field(default_factory=list)

    def add(self, question, answer):
        self.history.append((question, answer))
        # TODO: 超出 max_turns 两倍时从头部裁剪,只保留最近 max_turns 轮
        # 提示: limit = self.max_turns * 2
        # 提示: if len(self.history) > limit: self.history = self.history[-limit:]
        raise NotImplementedError("t74-acceptance-s2 尚未实现:请按 TODO 提示实现记忆裁剪")

    def recent(self, n=3):
        return self.history[-n * 2:]


TOOL_TABLE = {"calc", "echo", "quote"}

_CALC = {
    "add": lambda a, b: a + b,
    "mul": lambda a, b: a * b,
    "pow": lambda a, b: a ** b,
}


def dispatch_tool(name, args):
    """白名单分派:只认 TOOL_TABLE 里的工具,calc 内部再查 _CALC。"""
    if name not in TOOL_TABLE:
        return f"未知工具 {name},可用的工具: {', '.join(sorted(TOOL_TABLE))}"
    # TODO: 按白名单分派 calc/echo/quote 三类工具
    # 提示: calc 分支:解包 (a, b, op),op 不在 _CALC 返回 f"未知运算 {op}",否则 return _CALC[op](a, b)
    # 提示: echo 分支直接 return args;quote 分支 return f"「{args}」"
    raise NotImplementedError("t74-acceptance-s2 尚未实现:请按 TODO 提示完成工具白名单分派")


def load_kb(text):
    """按 --- 分隔符把整份素材切成知识块列表。"""
    return [c.strip() for c in text.split("---")]


def retrieve(query, kb, top_k=3):
    """按词频打分,返回最相关的 top_k 个知识块。"""
    q_words = query.split()
    scored = [(c, sum(c.count(w) for w in q_words), i) for i, c in enumerate(kb)]
    hits = sorted((t for t in scored if t[1] > 0), key=lambda t: t[1], reverse=True)
    return hits[:top_k]


def format_answer(hits):
    """把命中结果排版成可直接回复的答案文本。"""
    if not hits:
        return "未检索到相关资料"
    return "\n".join(f"[{i}] {c}(来源片段 {n})" for i, (c, s, n) in enumerate(hits, 1))


def run_tests(work_dir):
    """把 TEST_CODE 写成 test_qa.py,再用 pytest 实跑验收。"""
    test_file = Path(work_dir) / "test_qa.py"
    names = "load_kb, retrieve, format_answer, ChatMemory, dispatch_tool"
    test_file.write_text(f"from __main__ import {names}\n" + TEST_CODE, encoding="utf-8")
    rc = pytest.main(["-q", "-o", "addopts=", "-p", "no:cacheprovider",
                      "--rootdir", str(work_dir), str(test_file)])
    assert rc == 0, f"pytest 未全过:rc={rc}"


def main():
    print("== 渡劫飞升 · 集成测试 s2 ==")
    m = ChatMemory()
    m.add("渡劫有几关", format_answer(retrieve("渡劫", load_kb("渡劫需渡雷劫\n\n---\n\n飞升需法器"))))
    print(dispatch_tool("calc", (3, 4, "mul")))
    print(dispatch_tool("echo", "护体法器"))
    print(dispatch_tool("quote", "仙路漫漫"))
    with tempfile.TemporaryDirectory() as d:
        run_tests(d)
    print("pytest 全部通过:10 个用例")


if __name__ == "__main__":
    main()
