"""Agent 运行时底座 · s4:手写 vs 框架——同一剧本两种写法

同样的「查时间 → 查工作流阶段 → 答复」剧本,手写循环用一个函数把
决策、执行、判定全部揉在一起;Agent 运行时底座则把状态摊进 AgentState,
由 AgentLoop 统一驱动。两种写法跑出相同结果,可维护性却天差地别。
"""


# === 学习契约（面向学生）===
# 本节目标：手写 vs 框架:同一剧本两种写法。完成后能把本节概念放入可运行的工程链路。
# 需要补写：len；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `get_time() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `list_meridians() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `run_tool(name: str) -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `evaluate_stop(state: AgentState, max_steps: int=10) -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `hand_written_loop(script: list) -> dict`：输入为签名中的参数；输出为 `dict`。用途：手写版:一个函数揉进全部逻辑,状态藏在局部变量里。
#   - `compare() -> None`：输入为签名中的参数；输出为 `None`。用途：对比两种写法的动作步数与信息字段数。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `AgentStatus`：承载本节状态/数据；重点方法：见类定义。
#   - `StopReason`：承载本节状态/数据；重点方法：见类定义。
#   - `AgentState`：承载本节状态/数据；重点方法：见类定义。
#   - `AgentLoop`：承载本节状态/数据；重点方法：run。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import time


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


class AgentState:
    """框架版的数据袋:状态、消息、动作、答复、步数五件套。"""

    def __init__(self):
        self.status = AgentStatus.IDLE
        self.messages = []
        self.actions = []
        self.reply = ""
        self.steps = 0


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


DEMO_SCRIPT = ["get_time", "list_meridians", "reply"]


class AgentLoop:
    """框架版:状态摊进 AgentState,循环统一驱动。"""

    def __init__(self, max_steps: int = 10):
        self.state = AgentState()
        self.max_steps = max_steps
        self.stop_reason = StopReason.NONE

    def run(self, script: list) -> str:
        state = self.state
        state.status = AgentStatus.RUNNING
        while True:
            reason = evaluate_stop(state, self.max_steps)
            if reason != StopReason.NONE:
                self.stop_reason = reason
                break
            decision = script[state.steps] if state.steps < len(script) else "get_time"
            state.steps += 1
            if decision == "reply":
                state.reply = "当前为上午时段,工作流已完成工具执行。"
                state.status = AgentStatus.DONE
            else:
                result = run_tool(decision)
                state.actions.append(decision)
                state.messages.append({"role": "tool", "name": decision, "content": result})
        return state.reply


def hand_written_loop(script: list) -> dict:
    """手写版:一个函数揉进全部逻辑,状态藏在局部变量里。"""
    actions = []
    messages = []
    reply = ""
    steps = 0
    # TODO: 手写循环——按剧本顺序执行动作,reply 时收场
    # 提示: while True 内先判 steps >= len(script) 就 break;再取
    #       decision = script[steps] 并 steps += 1;decision == "reply" 时写
    #       reply 并 break;否则 result = run_tool(decision),把动作名与
    #       工具消息分别 append 进 actions / messages(role 用 "tool")
    raise NotImplementedError("hand_written_loop 尚未实现:请按 TODO 提示补全手写循环")
    return {"reply": reply, "actions": actions, "steps": steps}


def compare() -> None:
    """对比两种写法的动作步数与信息字段数。"""
    manual = hand_written_loop(DEMO_SCRIPT)
    loop = AgentLoop(max_steps=10)
    loop.run(DEMO_SCRIPT)
    print(f"手写版:  动作 {len(manual['actions'])} 步,信息字段 {len(manual)} 个")
    # TODO: 打印Agent 运行时底座分支——动作数取 len(loop.state.actions),字段数取 len(loop.state.__dict__)
    # 提示: print(f"Agent 运行时底座:  动作 {len(loop.state.actions)} 步,信息字段 {len(loop.state.__dict__)} 个")
    raise NotImplementedError("compare 尚未实现:请按 TODO 提示打印Agent 运行时底座分支")
    print(f"终止原因: {loop.stop_reason}")


def main() -> None:
    manual = hand_written_loop(DEMO_SCRIPT)
    print("手写版结果:", manual)
    loop = AgentLoop(max_steps=10)
    loop.run(DEMO_SCRIPT)
    print("Agent 运行时底座结果:", loop.state.reply)
    compare()


if __name__ == "__main__":
    main()
