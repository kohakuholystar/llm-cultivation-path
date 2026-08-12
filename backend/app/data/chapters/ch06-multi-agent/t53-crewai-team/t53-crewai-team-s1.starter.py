"""校园 AI 社 · s1：创建真实 CrewAI Agent，而不是自定义同名类。"""


# === 学习契约（面向学生）===
# 本节目标：对照原型：CrewAI Agent 角色卡。完成后能把本节概念放入可运行的工程链路。
# 需要补写：LLM；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `build_llm() -> LLM`：输入为签名中的参数；输出为 `LLM`。用途：按本节调用链完成对应处理
#   - `build_heaven(llm: LLM) -> list[Agent]`：输入为签名中的参数；输出为 `list[Agent]`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：需要在右上角 AI 配置填写自己的 DeepSeek API Key，并允许本节联网运行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import os
import sys

from crewai import Agent, LLM


def build_llm() -> LLM:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("请先在右上角 AI 配置填入 DeepSeek API Key，然后重新运行。")
        sys.exit(2)
    # TODO: 返回 LLM(model=f"openai/{MODEL_NAME}", api_key=api_key, base_url=..., temperature=0)。
    raise NotImplementedError("请配置真实 CrewAI LLM")


def build_heaven(llm: LLM) -> list[Agent]:
    # TODO: 返回 4 个 CrewAI Agent；每个具备 role、goal、backstory 和 llm。
    raise NotImplementedError("请创建真实 CrewAI Agent")


if __name__ == "__main__":
    for agent in build_heaven(build_llm()):
        print(f"{agent.role}: {agent.goal}")
