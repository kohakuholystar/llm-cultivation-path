"""乾坤圈 · s6:收官实战——完整演练与运行报告

本步给乾坤圈加上运行轨迹 trail:每一步执行后都留下一张
「快照」,跑完再输出三段式报告——运行轨迹、统计、终止原因。
至此,一个带状态机、生命周期、终止条件与观测能力的最小
Agent 运行时全部成形。
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
    """终极版乾坤圈:带运行轨迹的完整循环。"""

    def __init__(self, max_steps: int = 10):
        self.state = AgentState()
        self.max_steps = max_steps
        self.stop_reason = StopReason.NONE
        self.trail: list[dict] = []

    def _record(self, plan: str, result: str = "") -> dict:
        """生成一条轨迹快照:计划、结果、当时状态与终止原因。"""
        # TODO: 生成一条轨迹快照——含 plan/result/status/reason 四个字段
        # 提示: 返回 dict:plan 与 result 直接用入参,status 取 self.state.status,
        #       reason 取 self.stop_reason
        raise NotImplementedError("_record 尚未实现:请按 TODO 提示返回四字段轨迹快照")

    def run(self, script: list) -> str:
        state = self.state
        state.status = AgentStatus.RUNNING
        state.actions = []
        state.messages = []
        state.steps = 0
        self.stop_reason = StopReason.NONE
        i = 0
        while True:
            reason = evaluate_stop(state, self.max_steps)
            if reason != StopReason.NONE:
                self.stop_reason = reason
                break
            decision = script[i] if i < len(script) else "get_time"
            i += 1
            if decision == "reply":
                state.reply = "乾坤圈: 时辰与经络俱明。"
                state.status = AgentStatus.DONE
                state.messages.append({"role": "assistant", "content": state.reply})
                reason = evaluate_stop(state, self.max_steps)
                if reason != StopReason.NONE:
                    self.stop_reason = reason
                # TODO: 记录本条轨迹快照(答复结果)
                # 提示: self.trail.append(self._record(decision, state.reply))
                raise NotImplementedError("run 尚未实现:请按 TODO 提示在 reply 分支追加轨迹")
                break
            result = run_tool(decision)
            state.actions.append(decision)
            state.messages.append({"role": "tool", "name": decision, "content": result})
            state.steps += 1
            # TODO: 记录本条轨迹快照(工具结果)
            # 提示: self.trail.append(self._record(decision, result))
            raise NotImplementedError("run 尚未实现:请按 TODO 提示在工具分支追加轨迹")
        return state.reply


def print_report(loop: AgentLoop) -> None:
    """三段式报告:运行轨迹 / 统计 / 终止原因。"""
    # TODO: 依次打印运行轨迹、统计、终止原因三段
    # 提示: 轨迹逐条 print(f"第{idx}步 [{rec['status']}/{rec['reason']}] 计划: {rec['plan']} -> {rec['result'][:12]}");
    #       统计 print(f"计划步数 {len(loop.trail)} | 实际动作 {len(loop.state.actions)} 步 | 历史消息 {len(loop.state.messages)} 条");
    #       原因 print(f"终止原因: {loop.stop_reason} | {REASON_TEXT.get(loop.stop_reason, '')}")
    raise NotImplementedError("print_report 尚未实现:请按 TODO 提示完成三段式报告")


def main() -> None:
    loop = AgentLoop(max_steps=5)
    loop.run(["get_time", "list_meridians", "reply"])
    print(f"最终答复: {loop.state.reply}")
    print_report(loop)


if __name__ == "__main__":
    main()
