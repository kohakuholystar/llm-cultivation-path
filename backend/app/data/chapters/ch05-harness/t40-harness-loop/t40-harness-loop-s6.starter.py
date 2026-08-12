"""Agent 运行时底座 · s6:收官实战——完整演练与运行报告

本步给Agent 运行时底座加上运行轨迹 trail:每一步执行后都留下一张
「快照」,跑完再输出三段式报告——运行轨迹、统计、终止原因。
至此,一个带状态机、生命周期、终止条件与观测能力的最小
Agent 运行时全部成形。
"""


# === 学习契约（面向学生）===
# 本节目标：收官实战:完整演练与运行报告。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `get_time() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `list_meridians() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `run_tool(name: str) -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `evaluate_stop(state: AgentState, max_steps: int=10) -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `print_report(loop: AgentLoop) -> None`：输入为签名中的参数；输出为 `None`。用途：三段式报告:运行轨迹 / 统计 / 终止原因。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `AgentStatus`：承载本节状态/数据；重点方法：见类定义。
#   - `StopReason`：承载本节状态/数据；重点方法：见类定义。
#   - `AgentState`：承载本节状态/数据；重点方法：见类定义。
#   - `AgentLoop`：承载本节状态/数据；重点方法：_record, run。
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
    """终极版Agent 运行时底座:带运行轨迹的完整循环。"""

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
                state.reply = "Agent 运行时底座: 时间与工作流状态已汇总。"
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
