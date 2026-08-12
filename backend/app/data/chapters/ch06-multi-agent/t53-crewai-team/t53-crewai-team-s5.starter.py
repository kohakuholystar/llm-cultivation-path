"""校园 AI 社 · s5：真实 CrewAI 团队项目收官。"""


# === 学习契约（面向学生）===
# 本节目标：对照原型：CrewAI 小型交付闭环。完成后能把本节概念放入可运行的工程链路。
# 需要补写：Path；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `build_llm() -> LLM`：输入为签名中的参数；输出为 `LLM`。用途：按本节调用链完成对应处理
#   - `build_crew(llm: LLM) -> Crew`：输入为签名中的参数；输出为 `Crew`。用途：按本节调用链完成对应处理
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：需要在右上角 AI 配置填写自己的 DeepSeek API Key，并允许本节联网运行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import os
import sys
from pathlib import Path

from crewai import Agent, Crew, LLM, Process, Task


def build_llm() -> LLM:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("请先在右上角 AI 配置填入 DeepSeek API Key，然后重新运行。")
        sys.exit(2)
    # TODO: 返回由用户 Key 驱动的 CrewAI LLM。
    raise NotImplementedError("请创建 CrewAI LLM")


def build_crew(llm: LLM) -> Crew:
    # TODO: 创建产品、后端、测试 Agent；创建有 context 依赖的三个 Task；返回 Process.sequential 的 Crew。
    raise NotImplementedError("请组装真实 CrewAI 项目")


def main() -> None:
    result = build_crew(build_llm()).kickoff()
    # TODO: 将 result.raw 写入 Path("校园 AI 社协作纪要.md")，明确 encoding="utf-8"。
    raise NotImplementedError("请落盘真实团队的交付")


if __name__ == "__main__":
    main()
