"""Agent 运行时底座 · s3:终止条件——四种方式叫停循环

s1 的保险丝只看步数,过于粗暴。本步把「何时停」提完成
evaluate_stop 判定器:正常完成、步数超限、计划为空、动作重复,
四种终止原因统一用 StopReason 枚举表达,循环只负责转,判定交给专职函数。
"""


# === 学习契约（面向学生）===
# 本节目标：终止条件:四种方式叫停循环。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `get_time() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `run_tool(name: str) -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `evaluate_stop(state: AgentState, plan: list, max_steps: int, repeat_limit: int=3) -> str`：输入为签名中的参数；输出为 `str`。用途：判定是否该停:按 完成→超步→空计划→重复 的优先级返回终止原因。
#   - `demo_normal() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `demo_max_steps() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `demo_empty() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `demo_repeat() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `AgentStatus`：承载本节状态/数据；重点方法：见类定义。
#   - `StopReason`：承载本节状态/数据；重点方法：见类定义。
#   - `AgentState`：承载本节状态/数据；重点方法：见类定义。
#   - `AgentLoop`：承载本节状态/数据；重点方法：make_planner, step, run。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
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
    labels = ["深夜", "凌晨", "凌晨", "清晨", "早晨", "上午", "中午", "下午", "下午", "傍晚", "夜间", "深夜"]
    return f"当前时间段:{labels[hour % 12]}"


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
    """Agent 运行时底座主循环:决策、执行、判定三分,终止原因留痕。"""

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
            state.reply = "当前为上午时段,工作流已完成工具执行。"
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
