"""Agent 运行时底座 · s2:Step 抽象——动作也要有生命周期

s1 的循环把「执行」揉进了一个函数,动作一多就难以扩展。
本步引入 Step 抽象:每个动作都过 prepare → execute → finish
三阶段,并发出结构化事件,由 Harness 统一调度、记录与回放。
"""


# === 学习契约（面向学生）===
# 本节目标：Step 抽象:动作也要有生命周期。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `get_time() -> str`：输入为签名中的参数；输出为 `str`。用途：返回当前时间段。
#   - `list_meridians() -> str`：输入为签名中的参数；输出为 `str`。用途：列出工作流主要阶段。
#   - `run_tool(name: str) -> str`：输入为签名中的参数；输出为 `str`。用途：工具分发器:按名字找到组件并执行。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `AgentStatus`：承载本节状态/数据；重点方法：见类定义。
#   - `Event`：承载本节状态/数据；重点方法：见类定义。
#   - `Step`：承载本节状态/数据；重点方法：prepare, execute, finish。
#   - `ToolStep`：承载本节状态/数据；重点方法：prepare, execute, finish。
#   - `ReplyStep`：承载本节状态/数据；重点方法：prepare, execute, finish。
#   - `Harness`：承载本节状态/数据；重点方法：build_step, _log, run, print_events。
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===



import time
from abc import ABC, abstractmethod
from dataclasses import dataclass


class AgentStatus:
    """Agent 生命周期状态机。"""

    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


def get_time() -> str:
    """返回当前时间段。"""
    hour = time.localtime().tm_hour
    labels = ["深夜", "凌晨", "凌晨", "清晨", "早晨", "上午", "中午", "下午", "下午", "傍晚", "夜间", "深夜"]
    return f"当前时间段:{labels[hour % 12]}"


def list_meridians() -> str:
    """列出工作流主要阶段。"""
    return "工作流阶段:接收请求、选择工具、执行工具、汇总答复"


TOOLS = {"get_time": get_time, "list_meridians": list_meridians}


def run_tool(name: str) -> str:
    """工具分发器:按名字找到组件并执行。"""
    if name not in TOOLS:
        return f"[未知工具] {name}"
    return TOOLS[name]()


@dataclass
class Event:
    """一次生命周期事件:阶段、步骤名、附加细节。"""

    phase: str
    step: str
    detail: str = ""


class Step(ABC):
    """动作的抽象基类:每个动作都过 prepare / execute / finish 三段。"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def prepare(self, ctx: dict) -> None:
        """执行前的准备:校验参数、检查前置条件。"""

    @abstractmethod
    def execute(self, ctx: dict) -> str:
        """真正干活:调用工具或直接作答,返回文本结果。"""

    @abstractmethod
    def finish(self, ctx: dict) -> None:
        """执行后的收尾:清理、记录副作用、更新状态。"""


class ToolStep(Step):
    """调用工具注册表中某个工具的步骤。"""

    def __init__(self, name: str, tool: str):
        super().__init__(name)
        self.tool = tool

    def prepare(self, ctx: dict) -> None:
        """校验工具确实存在,不存在就在进入 execute 前报错。"""
        # TODO: 校验 self.tool 确实在 TOOLS 里,不在就抛 KeyError 并给出中文提示
        # 提示: 判 if self.tool not in TOOLS,成立则 raise KeyError(f"工具注册表中没有 {self.tool} 这件组件")
        raise NotImplementedError("prepare 尚未实现:请按 TODO 提示完成工具存在性校验")

    def execute(self, ctx: dict) -> str:
        result = run_tool(self.tool)
        ctx["actions"].append(self.tool)
        return result

    def finish(self, ctx: dict) -> None:
        ctx["messages"].append({"role": "tool", "name": self.tool, "content": ctx["last_result"]})


class ReplyStep(Step):
    """直接给用户答复的步骤。"""

    def prepare(self, ctx: dict) -> None:
        pass

    def execute(self, ctx: dict) -> str:
        return ctx["reply_text"]

    def finish(self, ctx: dict) -> None:
        ctx["status"] = AgentStatus.DONE


class Harness:
    """Agent 运行时底座调度器:按计划把步骤接成流水线,并记录生命周期事件。"""

    def __init__(self, plan: list):
        self.plan = plan
        self.events: list[Event] = []
        self.ctx = {
            "actions": [],
            "messages": [],
            "reply_text": "当前为上午时段,系统运行状态正常。",
            "last_result": "",
            "status": AgentStatus.RUNNING,
        }

    def build_step(self, spec: dict) -> Step:
        """按规格构建 Step:tool 规格造 ToolStep,其余造 ReplyStep。"""
        if spec["type"] == "tool":
            return ToolStep(spec["name"], spec["tool"])
        return ReplyStep(spec["name"])

    def _log(self, phase: str, step: str, detail: str = "") -> None:
        self.events.append(Event(phase, step, detail))

    def run(self) -> str:
        """按计划调度:每个步骤都走 prepare → execute → finish。"""
        # TODO: 调度循环——每个步骤依次 prepare → execute → finish,每阶段用 self._log 记录
        # 提示: for spec in self.plan:先 step = self.build_step(spec) 并 step.prepare(self.ctx)、
        #       self._log("prepare", step.name);再 result = step.execute(self.ctx) 回写
        #       self.ctx["last_result"]、self._log("execute", step.name, result[:14]);
        #       然后 step.finish(self.ctx)、self._log("finish", step.name);
        #       若 self.ctx["status"] != AgentStatus.RUNNING 立即 break
        raise NotImplementedError("run 尚未实现:请按 TODO 提示完成三阶段调度循环")
        return self.ctx["reply_text"]

    def print_events(self) -> None:
        print("\n== 事件回放 ==")
        for ev in self.events:
            print(f"  [{ev.phase:<8}] {ev.step}  {ev.detail}")


def main() -> None:
    plan = [
        {"type": "tool", "name": "get_time", "tool": "get_time"},
        {"type": "tool", "name": "list_meridians", "tool": "list_meridians"},
        {"type": "reply", "name": "reply"},
    ]
    h = Harness(plan)
    reply = h.run()
    print(f"答复: {reply}")
    h.print_events()
    print(f"状态: {h.ctx['status']} | 历史消息: {len(h.ctx['messages'])} 条")


if __name__ == "__main__":
    main()
