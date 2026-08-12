"""校园 AI 社 · s3：用真实 CrewAI 建立顺序团队。

Key 来自右上角配置注入的 OPENAI_API_KEY；不要把 Key 写进本文件。
"""


# === 学习契约（面向学生）===
# 本节目标：对照原型：CrewAI 顺序团队。完成后能把本节概念放入可运行的工程链路。
# 需要补写：Crew；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `build_llm() -> LLM`：输入为签名中的参数；输出为 `LLM`。用途：按本节调用链完成对应处理
#   - `build_agents(llm: LLM) -> dict[str, Agent]`：输入为签名中的参数；输出为 `dict[str, Agent]`。用途：按本节调用链完成对应处理
#   - `build_tasks(agents: dict[str, Agent]) -> list[Task]`：输入为签名中的参数；输出为 `list[Task]`。用途：按本节调用链完成对应处理
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：需要在右上角 AI 配置填写自己的 DeepSeek API Key，并允许本节联网运行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import os
import sys

from crewai import Agent, Crew, LLM, Process, Task


def build_llm() -> LLM:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("请先在右上角 AI 配置填入 DeepSeek API Key，然后重新运行。")
        sys.exit(2)
    # TODO: 返回 CrewAI LLM。model 使用 f"openai/{MODEL_NAME}"，并传入 api_key、base_url、temperature=0。
    raise NotImplementedError("请创建真实的 CrewAI LLM")


def build_agents(llm: LLM) -> dict[str, Agent]:
    # TODO: 创建产品经理、后端工程师、测试工程师三个 Agent；每个都传入 llm。
    raise NotImplementedError("请创建三个 CrewAI Agent")


def build_tasks(agents: dict[str, Agent]) -> list[Task]:
    # TODO: 创建需求、API、验收三个 Task；后两个分别用 context 引用上游 Task。
    raise NotImplementedError("请创建带 context 的 CrewAI Task")


def main() -> None:
    llm = build_llm()
    agents = build_agents(llm)
    # TODO: 使用 Crew(..., process=Process.sequential) 组装团队，调用 kickoff()，打印 result.raw。
    raise NotImplementedError("请启动真实 CrewAI 顺序流程")


if __name__ == "__main__":
    main()
