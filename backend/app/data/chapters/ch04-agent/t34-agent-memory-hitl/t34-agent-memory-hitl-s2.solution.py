"""百宝囊 · s2:危险操作中断确认
在记忆基座上挂工具,并给危险操作加一道「人工闸门」。
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
SYSTEM_PROMPT = ("你是「百宝囊」法宝管家。决定调用工具还是直接回答,只输出 JSON: "
                 '{"tool": 工具名或 null, "args": {...}, "reply": "回答"}。'
                 "可用工具: get_time()、delete_file(path)。")


@dataclass
class ChatMemory:
    """短期对话记忆(s1 成果,直接沿用)。"""

    max_turns: int = 10
    messages: list[dict] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.messages = self.messages[-self.max_turns * 2:]   # 只留最近 N 轮

    def history(self) -> list[dict]:
        return list(self.messages)


TOOLS = {                                          # 工具注册表:risky 标记危险度
    "get_time": {"fn": lambda: datetime.now().strftime("%H:%M:%S"), "risky": False},
    "delete_file": {"fn": lambda path: os.remove(path) or f"已删除 {path}", "risky": True},
}


def confirm_risky(tool: str, args: dict) -> bool:
    """人工闸门:危险操作执行前必须征得同意。"""
    print(f"[中断] 百宝囊请求执行危险操作 {tool}{args}")
    if MOCK:
        print("[中断] (演示)用户选择: n")
        return False                               # 演示模式默认拒绝,保护现场
    return input("允许执行吗? [y/N] ").strip().lower() == "y"


def run_tool(name: str, args: dict) -> str:
    """执行工具:危险操作先过闸门,异常不炸 Agent。"""
    spec = TOOLS.get(name)
    if spec is None:
        return f"未知工具: {name}"
    if spec["risky"] and not confirm_risky(name, args):   # 闸门:不点头就拦截
        return "操作已取消:用户拒绝了这次危险操作"
    try:
        return spec["fn"](**args)
    except Exception as exc:
        return f"工具执行失败: {exc}"


class LLM:
    """统一的真实/剧本 LLM 入口。"""

    def __init__(self, client, script=None):
        self.client = client
        self.script = list(script or [])

    def chat(self, messages):
        if self.client is None:
            return self.script.pop(0) if self.script else "(剧本已用完)"
        resp = self.client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0
        )
        return resp.choices[0].message.content


def handle(llm: LLM, memory: ChatMemory, user_input: str) -> str:
    """一轮请求:存记忆 → 模型决策 → (闸门)执行 → 回复入记忆。"""
    memory.add("user", user_input)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + memory.history()
    raw = llm.chat(messages)
    try:
        decision = json.loads(raw)                 # 期望模型输出 JSON 决策
    except json.JSONDecodeError:
        decision = {"tool": None, "args": {}, "reply": raw}
    reply = decision.get("reply", "")
    if decision.get("tool"):
        result = run_tool(decision["tool"], decision.get("args", {}))
        reply = f"{reply}(工具结果: {result})"
    memory.add("assistant", reply)
    return reply


def main() -> None:
    with open("notes.txt", "w", encoding="utf-8") as f:   # 演示用文件
        f.write("周五前提交百宝囊设计稿。")
    client = None
    if not MOCK:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                        base_url=BASE_URL, timeout=30, max_retries=0)
    script = [
        '{"tool": "get_time", "args": {}, "reply": "现在时间是"}',
        '{"tool": null, "args": {}, "reply": "好的,我记住了。"}',
        '{"tool": "delete_file", "args": {"path": "notes.txt"}, "reply": "好的"}',
    ]
    llm = LLM(client, script)
    memory = ChatMemory()
    for q in ["现在几点了?", "我叫阿黎,记一下", "把 notes.txt 删掉"]:
        print(f"\\n我: {q}")
        print(f"百宝囊: {handle(llm, memory, q)}")
    print(f"\\n[检查] notes.txt 是否还在: {os.path.exists('notes.txt')}")


if __name__ == "__main__":
    main()
