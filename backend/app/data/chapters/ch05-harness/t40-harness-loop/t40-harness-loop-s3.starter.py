"""乾坤圈 · s3:终止条件——四种方式叫停循环

s1 的保险丝只看步数,过于粗暴。本步把「何时停」提炼成
evaluate_stop 判定器:正常完成、步数超限、计划为空、动作重复,
四种终止原因统一用 StopReason 枚举表达,循环只负责转,判定交给专职函数。
"""
import time
from dataclasses import dataclass, field


class AgentStatus:
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class StopReason:
    NONE = "none"
    DONE = "done"
    MAX_STEPS = "max_steps"
    EMPTY_PLAN = "empty_plan"
    REPEAT = "repeat"


REASON_TEXT = {
    StopReason.DONE: "任务完成,正常收敛",
    StopReason.MAX_STEPS: "步数超限,保险丝熔断",
    StopReason.EMPTY_PLAN: "计划为空,无事可做",
    StopReason.REPEAT: "动作重复,疑似死循环",
}


@dataclass
class AgentState:
    messages: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    reply: str = ""
    status: str = AgentStatus.IDLE
    steps: int = 0


def get_time() -> str:
    hour = time.localtime().tm_hour
    labels = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    return f"现在是{labels[hour % 12]}时"


def run_tool(name: str) -> str:
    tools = {"get_time": get_time}
    if name not in tools:
        return f"[未知工具] {name}"
    return tools[name]()


def evaluate_stop(state: AgentState, plan: list, max_steps: int, repeat_limit: int = 3) -> str:
    """判定是否该停:按 完成→超步→空计划→重复 的优先级返回终止原因。"""
    # TODO: 依次检查四种终止条件,都未触发就返回 StopReason.NONE
    # 提示: 按序判断——state.status == AgentStatus.DONE 返 DONE;
    #       state.steps >= max_steps 返 MAX_STEPS;not plan 返 EMPTY_PLAN;
    #       state.actions[-repeat_limit:] 切片长度等于 repeat_limit
    #       且 set 去重后只剩一个元素返 REPEAT;末尾 return StopReason.NONE
    raise NotImplementedError("evaluate_stop 尚未实现:请按 TODO 提示完成四态判定")


class AgentLoop:
    """乾坤圈主循环:决策、执行、判定三分,终止原因留痕。"""

    def __init__(self, max_steps: int = 10):
        self.state = AgentState()
        self.max_steps = max_steps
        self.stop_reason = StopReason.NONE

    def make_planner(self, script: list):
        """把剧本包装成「每轮给一个动作」的规划器。"""

        def planner(state: AgentState) -> list:
            step = state.steps
            if step < len(script):
                return [script[step]]
            return []

        return planner

    def step(self, decision: str) -> str:
        """执行单个动作:reply 收场,工具调用记录进 state。"""
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

    def run(self, planner) -> str:
        """决策→执行→判定,直到 evaluate_stop 给出终止原因。"""
        state = self.state
        state.status = AgentStatus.RUNNING
        while True:
            plan = planner(state)
            reason = evaluate_stop(state, plan, self.max_steps)
            if reason != StopReason.NONE:
                # TODO: 记录终止原因,并按 超步/空计划/重复 打印 [超步]/[无动作]/[死循环] 提示
                # 提示: 先 self.stop_reason = reason;再 if reason == StopReason.MAX_STEPS:
                #       打印 f"[超步] 超过 {self.max_steps} 步仍未收敛,保险丝熔断";
                #       elif reason == StopReason.EMPTY_PLAN 打印 "[无动作] 计划为空,无事可做";
                #       elif reason == StopReason.REPEAT 打印 "[死循环] 连续重复同一动作,强制叫停"
                raise NotImplementedError("run 尚未实现:请按 TODO 提示完成叫停记录与提示")
                break
            decision = plan[0]
            out = self.step(decision)
            print(f"  [{state.status}] {decision} -> {out[:16]}")
        # TODO: 打印终止原因值与 REASON_TEXT 译文,再返回答复
        # 提示: print(f"原因: {self.stop_reason} | {REASON_TEXT.get(self.stop_reason, '')}")
        raise NotImplementedError("run 尚未实现:请按 TODO 提示打印终止原因译文")
        return state.reply


def demo_normal() -> None:
    loop = AgentLoop(max_steps=5)
    print("== 正常收敛 ==")
    loop.run(loop.make_planner(["get_time", "reply"]))
    print(f"执行动作数: {len(loop.state.actions)}")


def demo_max_steps() -> None:
    loop = AgentLoop(max_steps=2)
    print("== 步数超限 ==")
    loop.run(loop.make_planner(["get_time", "get_time", "get_time"]))
    print(f"执行动作数: {len(loop.state.actions)}")


def demo_empty() -> None:
    loop = AgentLoop(max_steps=5)
    print("== 计划为空 ==")
    loop.run(lambda state: [])
    print(f"执行动作数: {len(loop.state.actions)}")


def demo_repeat() -> None:
    loop = AgentLoop(max_steps=5)
    print("== 重复动作 ==")
    loop.run(lambda state: ["get_time"])
    print(f"执行动作数: {len(loop.state.actions)}")


if __name__ == "__main__":
    demo_normal()
    demo_max_steps()
    demo_empty()
    demo_repeat()
