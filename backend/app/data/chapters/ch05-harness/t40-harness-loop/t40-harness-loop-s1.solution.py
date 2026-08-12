"""Agent 运行时底座 · s1:状态机基座

Agent 运行时底座是本课程的 Agent 运行时组件,也是本课程「通用 Agent 运行时」的心脏。
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


# —— Agent 运行时底座的「工具注册表」:两个流程演示工具 ——
def get_time() -> str:
    """返回当前时间段。"""
    hour = time.localtime().tm_hour
    labels = ["深夜", "凌晨", "凌晨", "清晨", "早晨", "上午", "中午", "下午", "下午", "傍晚", "夜间", "深夜"]
    return f"当前时间段:{labels[hour % 12]}"


def list_meridians() -> str:
    """列出工作流主要阶段。"""
    return "工作流阶段:接收请求、选择工具、执行工具、汇总答复"


def run_tool(name: str) -> str:
    """工具分发器:按名字找到组件并执行。"""
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
    """Agent 运行时底座主循环:决策 → 执行 → 判定,三步一轮。"""

    def __init__(self, max_steps: int = 10):
        self.state = AgentState()
        self.max_steps = max_steps

    def _execute(self, decision: str) -> str:
        """执行阶段:reply 直接作答并收敛,其余交给 run_tool 分派。"""
        state = self.state
        state.steps += 1
        if decision == "reply":
            state.reply = "当前为上午时段,工作流已完成工具执行。"
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
