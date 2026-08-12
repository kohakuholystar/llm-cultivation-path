"""校园 AI 社 · s2：用真实 CrewAI Task 连接上游产出。"""


# === 学习契约（面向学生）===
# 本节目标：对照原型：CrewAI Task 依赖。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `build_llm() -> LLM`：输入为签名中的参数；输出为 `LLM`。用途：按本节调用链完成对应处理
#   - `build_plan(llm: LLM) -> list[Task]`：输入为签名中的参数；输出为 `list[Task]`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：需要在右上角 AI 配置填写自己的 DeepSeek API Key，并允许本节联网运行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import os
import sys

from crewai import Agent, LLM, Task


def build_llm() -> LLM:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("请先在右上角 AI 配置填入 DeepSeek API Key，然后重新运行。")
        sys.exit(2)
    # TODO: 创建使用右上角 Key 的 CrewAI LLM。
    raise NotImplementedError("请配置 CrewAI LLM")


def build_plan(llm: LLM) -> list[Task]:
    # TODO: 创建两个真实 Agent 和两个 Task；第二个 Task 用 context=[第一个 Task]。
    raise NotImplementedError("请创建带依赖的 CrewAI Task")


if __name__ == "__main__":
    for index, task in enumerate(build_plan(build_llm()), 1):
        print(f"任务 {index}: {task.description}")
