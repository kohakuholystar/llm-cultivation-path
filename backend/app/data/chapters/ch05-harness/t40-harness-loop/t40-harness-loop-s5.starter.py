"""乾坤圈 · s5:多轮会话——让运行时常住下来

s4 的循环跑完一轮就散场。真实 Agent 要陪用户聊很多轮,
本步给乾坤圈加上会话层:每轮输入都完整走一遍循环,
但消息历史跨轮保留——Agent 记得上一轮说过什么。
"""
import time
from dataclasses import dataclass, field


class AgentStatus:
    IDLE = "idle"; RUNNING = "running"; DONE = "done"; ERROR = "error"


class StopReason:
    NONE = "none"; DONE = "done"; MAX_STEPS = "max_steps"
    EMPTY_PLAN = "empty_plan"; REPEAT = "repeat"


REASON_TEXT = {
    StopReason.DONE: "任务完成",
    StopReason.MAX_STEPS: "步数超限",
    StopReason.EMPTY_PLAN: "计划为空",
    StopReason.REPEAT: "动作重复",
}


@dataclass
class AgentState:
    """运行数据袋:消息历史跨轮累积,其余字段每轮重置。"""

    status: str = AgentStatus.IDLE
    messages: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    reply: str = ""
    steps: int = 0


def get_time() -> str:
    hour = time.localtime().tm_hour
    labels = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    return f"现在是{labels[hour % 12]}时"


def list_meridians() -> str:
    return "十二经脉:手太阴肺经、手阳明大肠经、足阳明胃经……"


TOOLS = {"get_time": get_time, "list_meridians": list_meridians}


def run_tool(name: str) -> str:
    if name not in TOOLS:
        return f"[未知工具] {name}"
    return TOOLS[name]()


def evaluate_stop(state: AgentState, max_steps: int = 10) -> str:
    if state.status == AgentStatus.DONE:
        return StopReason.DONE
    if state.steps >= max_steps:
        return StopReason.MAX_STEPS
    last_three = state.actions[-3:]
    if len(last_three) == 3 and len(set(last_three)) == 1:
        return StopReason.REPEAT
    return StopReason.NONE


class AgentLoop:
    """单轮循环:run 开头重置本轮数据,消息历史跨轮保留。"""

    def __init__(self, max_steps: int = 10):
        self.state = AgentState()
        self.max_steps = max_steps
        self.stop_reason = StopReason.NONE

    def run(self, user_input: str, script: list) -> str:
        state = self.state
        state.status = AgentStatus.RUNNING
        state.steps = 0
        state.actions = []
        state.reply = ""
        self.stop_reason = StopReason.NONE
        state.messages.append({"role": "user", "content": user_input})
        while True:
            reason = evaluate_stop(state, self.max_steps)
            if reason != StopReason.NONE:
                self.stop_reason = reason
                break
            decision = script[state.steps] if state.steps < len(script) else "get_time"
            state.steps += 1
            if decision == "reply":
                state.reply = f"收到:{user_input}——已记下。"
                state.status = AgentStatus.DONE
            else:
                result = run_tool(decision)
                state.actions.append(decision)
                state.messages.append({"role": "tool", "name": decision, "content": result})
        return state.reply


@dataclass
class TurnRecord:
    """一轮对话的记录:轮次、结束时状态、本轮动作数。"""

    turn: int
    status: str
    actions: int


class AgentSession:
    """会话层:带着消息历史连续跑多轮。"""

    def __init__(self, loop: AgentLoop):
        self.loop = loop
        self.turns: list[TurnRecord] = []

    def run(self, user_input: str, script: list) -> str:
        # TODO: 跑一轮——调用 self.loop.run(user_input, script),再把本轮记录追加进 turns
        # 提示: 先 self.loop.run(user_input, script);再构造
        #       TurnRecord(len(self.turns) + 1, self.loop.state.status,
        #       len(self.loop.state.actions)) 并 self.turns.append(...)
        raise NotImplementedError("run 尚未实现:请按 TODO 提示补全单轮会话记录")
        return self.loop.state.reply

    def report(self) -> None:
        for rec in self.turns:
            print(f"第{rec.turn}轮 [{rec.status}] 动作 {rec.actions} 步")
        total_actions = sum(rec.actions for rec in self.turns)
        print(f"共 {len(self.turns)} 轮,动作 {total_actions} 步,消息历史 {len(self.loop.state.messages)} 条")


def main() -> None:
    loop = AgentLoop(max_steps=10)
    session = AgentSession(loop)
    session.run("现在是什么时辰?", ["get_time", "reply"])
    session.run("十二经脉有哪些?", ["get_time", "reply"])
    session.run("我们改天再聊", ["reply"])
    session.report()


if __name__ == "__main__":
    main()
