"""校园 AI 社 · s4：使用 CrewAI 的 hierarchical 流程。"""


# === 学习契约（面向学生）===
# 本节目标：对照原型：CrewAI 层级团队。完成后能把本节概念放入可运行的工程链路。
# 需要补写：LLM、Crew；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `build_llm() -> LLM`：输入为签名中的参数；输出为 `LLM`。用途：按本节调用链完成对应处理
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
    # TODO: 创建 LLM(model=f"openai/{MODEL_NAME}", api_key=..., base_url=..., temperature=0)。
    raise NotImplementedError("请创建 CrewAI LLM")


def main() -> None:
    llm = build_llm()
    # TODO: 创建一个 Agent 和一个最小 Task；用 Crew(process=Process.hierarchical, manager_llm=llm) 启动。
    # 真实框架负责总管调度；不要自己定义名为 Crew 的类或模拟 manager。
    raise NotImplementedError("请启动真实 CrewAI 层级流程")


if __name__ == "__main__":
    main()
