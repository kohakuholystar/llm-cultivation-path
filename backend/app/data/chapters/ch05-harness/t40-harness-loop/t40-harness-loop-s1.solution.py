"""乾坤圈 · s1:状态机基座

乾坤圈是神话里可大可小的法宝,也是本课程「通用 Agent 运行时」的心脏。
本步从零搭出最精简的循环骨架:状态(AgentStatus)、数据(AgentState)、
循环(AgentLoop)三层分离;决策暂由剧本 scripted_decide 充当「模型大脑」,
再装上一根 max_steps 保险丝,防止剧本失灵时无限空转。
"""
import time
from dataclasses import dataclass, field


class AgentStatus:
    """Agent 生命周期状态机:空闲 → 运行中 → 完成 / 出错。"""

    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


@dataclass
class AgentState:
    """一次循环运行的数据袋:消息历史、动作记录、答复与状态。"""

    messages: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    reply: str = ""
    status: str = AgentStatus.IDLE
    steps: int = 0


# —— 乾坤圈的「法宝库」:两个时辰类小工具 ——
def get_time() -> str:
    """报当前时辰(十二时辰制)。"""
    hour = time.localtime().tm_hour
    labels = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    return f"现在是{labels[hour % 12]}时"


def list_meridians() -> str:
    """列出十二经脉名。"""
    return "十二经脉:手太阴肺经、手阳明大肠经、足阳明胃经……"


def run_tool(name: str) -> str:
    """工具分发器:按名字找到法宝并执行。"""
    tools = {"get_time": get_time, "list_meridians": list_meridians}
    if name not in tools:
        return f"[未知工具] {name}"
    return tools[name]()


def scripted_decide(state: AgentState, script: list) -> str:
    """脚本决策器:按剧本顺序给动作,演完就退回 get_time 卡循环。"""
    step = state.steps
    if step < len(script):
        return script[step]
    return "get_time"


class AgentLoop:
    """乾坤圈主循环:决策 → 执行 → 判定,三步一轮。"""

    def __init__(self, max_steps: int = 10):
        self.state = AgentState()
        self.max_steps = max_steps

    def _execute(self, decision: str) -> str:
        """执行阶段:reply 直接作答并收敛,其余交给 run_tool 分派。"""
        state = self.state
        state.steps += 1
        if decision == "reply":
            state.reply = "巳时三刻,气血行至手阳明大肠经。"
            state.status = AgentStatus.DONE
            return state.reply
        result = run_tool(decision)
        state.actions.append(decision)
        state.messages.append({"role": "tool", "name": decision, "content": result})
        return result

    def run(self, script: list, label: str = "演示一:正常收敛") -> str:
        """主循环:决策→执行→判定,直到收敛或保险丝熔断。"""
        print(f"== {label} ==")
        self.state.status = AgentStatus.RUNNING
        while self.state.status == AgentStatus.RUNNING:
            decision = scripted_decide(self.state, script)
            out = self._execute(decision)
            print(f"  [{self.state.status}] {decision} -> {out[:18]}")
            if self.state.status == AgentStatus.DONE:
                break
            if self.state.steps >= self.max_steps:
                self.state.status = AgentStatus.ERROR
                print(f"[超步] 超过 {self.max_steps} 步仍未收敛,保险丝熔断")
                break
        print(f"最终状态: {self.state.status}")
        print(f"动作序列: {self.state.actions}")
        return self.state.reply


def demo_normal() -> None:
    loop = AgentLoop(max_steps=10)
    loop.run(["get_time", "list_meridians", "reply"])


def demo_fuse() -> None:
    loop = AgentLoop(max_steps=3)
    loop.run(["get_time", "get_time", "get_time", "get_time"], label="演示二:保险丝熔断")


if __name__ == "__main__":
    demo_normal()
    demo_fuse()
