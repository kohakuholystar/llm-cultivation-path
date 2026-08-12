"""Agent 运行时底座 · s1:状态机基座

Agent 运行时底座是本课程的 Agent 运行时组件,也是本课程「通用 Agent 运行时」的心脏。
本步从零搭出最精简的循环骨架:状态(AgentStatus)、数据(AgentState)、
循环(AgentLoop)三层分离;决策暂由剧本 scripted_decide 充当「模型大脑」,
再装上一根 max_steps 保险丝,防止剧本失灵时无限空转。
"""


# === 学习契约（面向学生）===
# 本节目标：状态机基座:Agent 运行时底座的心脏开始跳动。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `get_time() -> str`：输入为签名中的参数；输出为 `str`。用途：返回当前时间段。
#   - `list_meridians() -> str`：输入为签名中的参数；输出为 `str`。用途：列出工作流主要阶段。
#   - `run_tool(name: str) -> str`：输入为签名中的参数；输出为 `str`。用途：工具分发器:按名字找到组件并执行。
#   - `scripted_decide(state: AgentState, script: list) -> str`：输入为签名中的参数；输出为 `str`。用途：脚本决策器:按剧本顺序给动作,演完就退回 get_time 卡循环。
#   - `demo_normal() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `demo_fuse() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `AgentStatus`：承载本节状态/数据；重点方法：见类定义。
#   - `AgentState`：承载本节状态/数据；重点方法：见类定义。
#   - `AgentLoop`：承载本节状态/数据；重点方法：_execute, run。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===



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
        # TODO: 执行一个动作——reply 直接写答复并置 DONE,其余交给 run_tool 分派
        # 提示: 开头 state = self.state 并 state.steps += 1;decision == "reply" 时写
        #       state.reply 并置 state.status = AgentStatus.DONE 后 return;
        #       否则 result = run_tool(decision),把动作名与工具消息分别
        #       append 进 state.actions / state.messages,最后 return result
        raise NotImplementedError("_execute 尚未实现:请按 TODO 提示补全 reply 与工具两条分支")

    def run(self, script: list, label: str = "演示一:正常收敛") -> str:
        print(f"== {label} ==")
        self.state.status = AgentStatus.RUNNING
        while self.state.status == AgentStatus.RUNNING:
            decision = scripted_decide(self.state, script)
            out = self._execute(decision)
            print(f"  [{self.state.status}] {decision} -> {out[:18]}")
            if self.state.status == AgentStatus.DONE:
                break
            # TODO: 保险丝——步数达到 max_steps 仍未收敛,置 ERROR 并打印 [超步] 提示后收场
            # 提示: 判 if self.state.steps >= self.max_steps;成立时置
            #       self.state.status = AgentStatus.ERROR、打印
            #       f"[超步] 超过 {self.max_steps} 步仍未收敛,保险丝熔断"、break
            raise NotImplementedError("run 尚未实现:请按 TODO 提示完成保险丝熔断")
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
