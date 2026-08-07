"""百宝囊 · s5:收官实战
记忆、工具、HITL 全装配的「百宝囊」,跑一段完整使用剧本并输出行动报告。
"""
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime

from openai import OpenAI

MOCK = os.environ.get("MOCK_LLM") == "1"          # 演示模式:无网时用剧本回复
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("请先在右上角 AI 配置填入 DeepSeek API Key")
    sys.exit(0)

BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
SYSTEM_PROMPT = ("你是「百宝囊」法宝管家,只输出 JSON 决策: "
                 '{"tool": 工具名或 null, "args": {...}, "reply": "回答"}。'
                 "可用工具: get_time()、delete_file(path)。")
TOOLS = {"get_time": {"fn": lambda: datetime.now().strftime("%H:%M:%S"), "risky": False},
         "delete_file": {"fn": lambda p: os.remove(p) or f"已删除 {p}", "risky": True}}


@dataclass
class ChatMemory:
    """短期对话记忆:超出 max_turns 轮就从最旧端裁剪。"""

    max_turns: int = 10
    messages: list[dict] = field(default_factory=list)

    def add(self, role, content):
        self.messages.append({"role": role, "content": content})
        self.messages = self.messages[-self.max_turns * 2:]

    def history(self):
        return list(self.messages)


class HITLController:
    """人机协同闸门:裁决危险操作并留下审计日志。"""

    def __init__(self, handler=None):
        self.handler = handler or (lambda t, a: ("n", "默认拒绝"))
        self.audit: list[dict] = []

    def gate(self, tool, args):
        print(f"[中断] 危险操作请求 {tool}{args}")
        d, note = self.handler(tool, args)
        self.audit.append({"tool": tool, "decision": d, "note": note})
        return d, note


def run_tool(name, args, hitl):
    """危险操作先过闸门;接管时机器绝不代劳。"""
    spec = TOOLS.get(name)
    if spec is None:
        return f"未知工具: {name}"
    if spec["risky"]:
        d, note = hitl.gate(name, args)
        if d == "n":
            return f"操作已取消: {note or '用户拒绝'}"
        if d == "t":
            return f"人工接管完成: {note or '已由人手工处理'}"
    try:
        return spec["fn"](**args)
    except Exception as exc:
        return f"工具执行失败: {exc}"


class LLM:
    """统一的真实/剧本 LLM 入口。"""

    def __init__(self, client, script=None):
        self.client, self.script = client, list(script or [])

    def chat(self, messages):
        if self.client is None:
            return self.script.pop(0) if self.script else "(剧本已用完)"
        r = self.client.chat.completions.create(model=MODEL, messages=messages,
                                                temperature=0)
        return r.choices[0].message.content


class BaibaonangAgent:
    """「百宝囊」完全体:记忆 + 工具 + HITL 闸门 + 步数保险丝。"""

    def __init__(self, llm, hitl, max_steps=4):
        self.llm, self.hitl, self.max_steps = llm, hitl, max_steps
        self.memory = ChatMemory()

    def chat(self, user_input):
        """ReAct 循环:决策 → 执行 → 结果喂回,直到最终回复。"""
        self.memory.add("user", user_input)
        for _ in range(self.max_steps):
            raw = self.llm.chat([{"role": "system", "content": SYSTEM_PROMPT}]
                                + self.memory.history())
            try:
                decision = json.loads(raw)
            except json.JSONDecodeError:
                decision = {"tool": None, "reply": raw}
            if not decision.get("tool"):
                reply = decision.get("reply", "")
                self.memory.add("assistant", reply)
                return reply
            result = run_tool(decision["tool"], decision.get("args", {}), self.hitl)
            self.memory.add("assistant", raw)
            self.memory.add("user", f"[工具结果] {result}")
        return "已达最大步数,转人工处理。"


def print_report(agent) -> None:
    """收官报告:记忆规模 + 人工干预审计。"""
    print("\\n===== 百宝囊行动报告 =====")
    print(f"对话记忆: {len(agent.memory.history())} 条")
    print("人工干预记录:" if agent.hitl.audit else "人工干预记录: 无(全部是安全操作)")
    for i, e in enumerate(agent.hitl.audit, 1):
        print(f"  {i}. {e['tool']} -> {e['decision']} ({e['note']})")


def main() -> None:
    open("design.txt", "w", encoding="utf-8").write("百宝囊设计稿")
    client = None if MOCK else OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                                      base_url=BASE_URL, timeout=30, max_retries=0)
    script = [                                   # 三问五答的完整使用剧本
        '{"tool": null, "args": {}, "reply": "记住了:你叫阿黎,喜欢纸质笔记。"}',
        '{"tool": "get_time", "args": {}, "reply": ""}',
        '{"tool": null, "args": {}, "reply": "阿黎,现在是喝茶时间。"}',
        '{"tool": "delete_file", "args": {"path": "design.txt"}, "reply": ""}',
        '{"tool": null, "args": {}, "reply": "明白,设计稿我替你保住了。"}',
    ]
    hitl = HITLController((lambda t, a: ("n", "设计稿不能删")) if MOCK else None)
    agent = BaibaonangAgent(LLM(client, script), hitl)
    for q in ["我叫阿黎,喜欢纸质笔记,记一下", "现在几点?我叫什么来着?", "把 design.txt 删掉"]:
        print(f"\\n我: {q}")
        print(f"百宝囊: {agent.chat(q)}")
    print_report(agent)
    print(f"[检查] design.txt 是否还在: {os.path.exists('design.txt')}")


if __name__ == "__main__":
    main()
