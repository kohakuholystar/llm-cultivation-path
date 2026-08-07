"""百宝囊 · s3:人工接管钩子
闸门升级为三态裁决:批准 / 拒绝 / 接管,并留下审计日志。
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


TOOLS = {
    "get_time": {"fn": lambda: datetime.now().strftime("%H:%M:%S"), "risky": False},
    "delete_file": {"fn": lambda path: os.remove(path) or f"已删除 {path}", "risky": True},
}


class HITLController:
    """人机协同闸门:裁决危险操作,并记录每一次干预。"""

    def __init__(self, handler=None):
        self.handler = handler or self._ask   # handler(tool, args) -> ("y"/"n"/"t", 备注)
        self.audit: list[dict] = []           # 审计日志:谁在何时干预了什么

    @staticmethod
    def _ask(tool, args):
        """真实模式默认裁决器:命令行询问用户。"""
        ans = input("允许执行? [y]批准/[N]拒绝/[t]接管 ").strip().lower() or "n"
        note = input("备注: ") if ans == "t" else ""
        return ("t" if ans == "t" else "y" if ans == "y" else "n"), note

    def gate(self, tool: str, args: dict) -> tuple[str, str]:
        """危险操作的唯一入口:先裁决、记审计,再放行。"""
        # TODO: 打印请求 → 取裁决 → 记审计 → 返回 (decision, note)
        # 提示: print(f"[中断] 危险操作请求 {tool}{args}");decision, note = self.handler(tool, args);self.audit.append({"tool": tool, "decision": decision, "note": note})
        raise NotImplementedError("t34-s3 尚未实现:请按 TODO 提示完成 gate")


def scripted_handler(queue):
    """演示用裁决器:按剧本依次给出 批准/拒绝/接管。"""
    def _handle(tool, args):
        decision, note = queue.pop(0) if queue else ("n", "剧本外一律拒绝")
        print(f"[中断] (演示)用户裁决: {decision} —— {note}")
        return decision, note
    return _handle


def run_tool(name: str, args: dict, hitl: HITLController) -> str:
    """执行工具:危险操作先过 HITL 闸门,接管时机器绝不代劳。"""
    spec = TOOLS.get(name)
    if spec is None:
        return f"未知工具: {name}"
    if spec["risky"]:
        decision, note = hitl.gate(name, args)
        if decision == "n":
            return f"操作已取消: {note or '用户拒绝'}"
        # TODO: 接管分支:机器退出,交给人来手工处理
        # 提示: if decision == "t": return f"人工接管完成: {note or '已由人手工处理'}"
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


def main() -> None:
    for name in ("old.log", "design.txt", "tmp.txt"):
        open(name, "w", encoding="utf-8").write("演示文件")
    client = None
    if not MOCK:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                        base_url=BASE_URL, timeout=30, max_retries=0)
    queue = [("y", "旧日志,批准"), ("n", "设计稿不能删"), ("t", "我手动备份后处理")]
    hitl = HITLController(scripted_handler(queue) if MOCK else None)
    llm = LLM(client)                          # 本步聚焦闸门,LLM 留待 s4 装配
    for f in ("old.log", "design.txt", "tmp.txt"):
        print("工具结果:", run_tool("delete_file", {"path": f}, hitl))
    print(f"[检查] old.log={os.path.exists('old.log')} "
          f"design.txt={os.path.exists('design.txt')} tmp.txt={os.path.exists('tmp.txt')}")
    print("\\n[审计日志]")
    for i, entry in enumerate(hitl.audit, 1):
        print(f"  {i}. {entry['tool']} -> {entry['decision']} ({entry['note']})")


if __name__ == "__main__":
    main()
