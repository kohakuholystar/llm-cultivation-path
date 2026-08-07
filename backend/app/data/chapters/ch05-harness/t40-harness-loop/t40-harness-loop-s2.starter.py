"""乾坤圈 · s2:Step 抽象——动作也要有生命周期

s1 的循环把「执行」揉进了一个函数,动作一多就难以扩展。
本步引入 Step 抽象:每个动作都过 prepare → execute → finish
三阶段,并发出结构化事件,由 Harness 统一调度、记录与回放。
"""
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
    """报当前时辰(十二时辰制)。"""
    hour = time.localtime().tm_hour
    labels = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    return f"现在是{labels[hour % 12]}时"


def list_meridians() -> str:
    """列出十二经脉名。"""
    return "十二经脉:手太阴肺经、手阳明大肠经、足阳明胃经……"


TOOLS = {"get_time": get_time, "list_meridians": list_meridians}


def run_tool(name: str) -> str:
    """工具分发器:按名字找到法宝并执行。"""
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
    """调用法宝库中某个工具的步骤。"""

    def __init__(self, name: str, tool: str):
        super().__init__(name)
        self.tool = tool

    def prepare(self, ctx: dict) -> None:
        """校验工具确实存在,不存在就在进入 execute 前报错。"""
        # TODO: 校验 self.tool 确实在 TOOLS 里,不在就抛 KeyError 并给出中文提示
        # 提示: 判 if self.tool not in TOOLS,成立则 raise KeyError(f"法宝库中没有 {self.tool} 这件法宝")
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
    """乾坤圈调度器:按计划把步骤接成流水线,并记录生命周期事件。"""

    def __init__(self, plan: list):
        self.plan = plan
        self.events: list[Event] = []
        self.ctx = {
            "actions": [],
            "messages": [],
            "reply_text": "现在是巳时,气血正旺。",
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
