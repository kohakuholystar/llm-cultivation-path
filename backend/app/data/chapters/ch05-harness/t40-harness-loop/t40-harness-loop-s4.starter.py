"""乾坤圈 · s4:手写 vs 框架——同一剧本两种写法

同样的「查时辰 → 查经络 → 答复」剧本,手写循环用一个函数把
决策、执行、判定全部揉在一起;乾坤圈则把状态摊进 AgentState,
由 AgentLoop 统一驱动。两种写法跑出相同结果,可维护性却天差地别。
"""
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
                state.reply = "巳时三刻,气血行至手阳明大肠经。"
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
    # TODO: 打印乾坤圈分支——动作数取 len(loop.state.actions),字段数取 len(loop.state.__dict__)
    # 提示: print(f"乾坤圈:  动作 {len(loop.state.actions)} 步,信息字段 {len(loop.state.__dict__)} 个")
    raise NotImplementedError("compare 尚未实现:请按 TODO 提示打印乾坤圈分支")
    print(f"终止原因: {loop.stop_reason}")


def main() -> None:
    manual = hand_written_loop(DEMO_SCRIPT)
    print("手写版结果:", manual)
    loop = AgentLoop(max_steps=10)
    loop.run(DEMO_SCRIPT)
    print("乾坤圈结果:", loop.state.reply)
    compare()


if __name__ == "__main__":
    main()
