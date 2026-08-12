"""社团工具箱 · s4:社团工具箱总装
记忆 + 工具 + HITL 闸门,装配成会思考、会请示的完整 Agent。
"""
# ????????????????????????BaibaonangAgent ?????????????????????????????????????????HITL????t34-s3???????Agent ???????????????
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
SYSTEM_PROMPT = ("你是「社团工具箱」工具管家。决定调用工具还是直接回答,只输出 JSON: "
                 '{"tool": 工具名或 null, "args": {...}, "reply": "回答"}。'
                 "可用工具: get_time()、delete_file(path)。")


@dataclass
class ChatMemory:
    """短期对话记忆:超出 max_turns 轮就从最旧端裁剪。"""

    max_turns: int = 10
    messages: list[dict] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.messages = self.messages[-self.max_turns * 2:]

    def history(self) -> list[dict]:
        return list(self.messages)


TOOLS = {
    "get_time": {"fn": lambda: datetime.now().strftime("%H:%M:%S"), "risky": False},
    "delete_file": {"fn": lambda path: os.remove(path) or f"已删除 {path}", "risky": True},
}


class HITLController:
    """人机协同闸门:裁决危险操作并留下审计日志(s3 成果)。"""

    def __init__(self, handler=None):
        self.handler = handler or (lambda t, a: ("n", "未配置裁决器,默认拒绝"))
        self.audit: list[dict] = []

    def gate(self, tool: str, args: dict) -> tuple[str, str]:
        print(f"[中断] 危险操作请求 {tool}{args}")
        decision, note = self.handler(tool, args)
        self.audit.append({"tool": tool, "decision": decision, "note": note})
        return decision, note


def run_tool(name: str, args: dict, hitl: HITLController) -> str:
    """执行工具:危险操作先过闸门,接管时机器绝不代劳。"""
    spec = TOOLS.get(name)
    if spec is None:
        return f"未知工具: {name}"
    if spec["risky"]:
        decision, note = hitl.gate(name, args)
        if decision == "n":
            return f"操作已取消: {note or '用户拒绝'}"
        if decision == "t":
            return f"人工接管完成: {note or '已由人手工处理'}"
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


class BaibaonangAgent:
    """「社团工具箱」完全体:记忆 + 工具 + HITL 闸门 + 步数保险丝。"""

    def __init__(self, llm: LLM, hitl: HITLController, max_steps: int = 4):
        self.llm = llm
        self.memory = ChatMemory()
        self.hitl = hitl
        self.max_steps = max_steps               # 保险丝:防止工具循环失控

    def chat(self, user_input: str) -> str:
        """ReAct 循环:决策 → 执行 → 结果喂回模型,直到给出最终回复。"""
        # TODO: 循环内解析模型 JSON 决策:无工具则存回复并返回;有工具则执行并把结果喂回记忆
        # 提示: json.loads(raw) 兜底 JSONDecodeError → {"tool": None, "reply": raw};run_tool(decision["tool"], decision.get("args", {}), self.hitl);超步数 return "已达最大步数,转人工处理。"
        raise NotImplementedError("t34-s4 尚未实现:请按 TODO 提示完成 ReAct 循环")


def main() -> None:
    open("old.log", "w", encoding="utf-8").write("过期日志")
    client = None
    if not MOCK:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                        base_url=BASE_URL, timeout=30, max_retries=0)
    script = [                                   # 一轮带工具的完整对话剧本
        '{"tool": "get_time", "args": {}, "reply": ""}',
        '{"tool": null, "args": {}, "reply": "现在是茶歇时间,要整理旧日志吗?"}',
        '{"tool": "delete_file", "args": {"path": "old.log"}, "reply": ""}',
        '{"tool": null, "args": {}, "reply": "旧日志已清理完毕。"}',
    ]
    hitl = HITLController((lambda t, a: ("y", "演示批准")) if MOCK else None)
    agent = BaibaonangAgent(LLM(client, script), hitl)
    print("我: 现在几点?顺便把 old.log 清掉")
    print("社团工具箱:", agent.chat("现在几点?"))
    print("社团工具箱:", agent.chat("把 old.log 删掉"))
    print(f"[检查] old.log 是否还在: {os.path.exists('old.log')}, "
          f"审计 {len(agent.hitl.audit)} 条,记忆 {len(agent.memory.history())} 条")


if __name__ == "__main__":
    main()
