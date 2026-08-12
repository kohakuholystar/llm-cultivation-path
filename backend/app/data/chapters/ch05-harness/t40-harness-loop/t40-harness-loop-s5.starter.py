"""Agent 运行时底座 · s5:多轮会话——让运行时常住下来

s4 的循环跑完一轮就散场。真实 Agent 要陪用户聊很多轮,
本步给Agent 运行时底座加上会话层:每轮输入都完整走一遍循环,
但消息历史跨轮保留——Agent 记得上一轮说过什么。
"""


# === 学习契约（面向学生）===
# 本节目标：多轮会话:让运行时常住下来。完成后能把本节概念放入可运行的工程链路。
# 需要补写：run；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `get_time() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `list_meridians() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `run_tool(name: str) -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `evaluate_stop(state: AgentState, max_steps: int=10) -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `AgentStatus`：承载本节状态/数据；重点方法：见类定义。
#   - `StopReason`：承载本节状态/数据；重点方法：见类定义。
#   - `AgentState`：承载本节状态/数据；重点方法：见类定义。
#   - `AgentLoop`：承载本节状态/数据；重点方法：run。
#   - `TurnRecord`：承载本节状态/数据；重点方法：见类定义。
#   - `AgentSession`：承载本节状态/数据；重点方法：run, report。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
    labels = ["深夜", "凌晨", "凌晨", "清晨", "早晨", "上午", "中午", "下午", "下午", "傍晚", "夜间", "深夜"]
    return f"当前时间段:{labels[hour % 12]}"


def list_meridians() -> str:
    return "工作流阶段:接收请求、选择工具、执行工具、汇总答复"


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
    session.run("当前是什么时间段?", ["get_time", "reply"])
    session.run("工作流有哪些主要阶段?", ["get_time", "reply"])
    session.run("我们改天再聊", ["reply"])
    session.report()


if __name__ == "__main__":
    main()
