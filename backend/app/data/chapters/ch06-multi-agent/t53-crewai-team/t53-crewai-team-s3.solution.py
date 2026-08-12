"""校园 AI 社 · s3：使用真实 CrewAI 顺序编排。

本步首次真正调用 CrewAI。请先在右上角配置自己的 DeepSeek Key；运行时
平台会把它注入 OPENAI_API_KEY，代码中不保存也不填写 Key。
"""
import os
import sys

from crewai import Agent, Crew, LLM, Process, Task


def require_key() -> str:
    """把凭据边界放在入口：没有学生自己的 Key 就不启动联网团队。"""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("请先在右上角 AI 配置填入 DeepSeek API Key，然后重新运行。")
        sys.exit(2)
    return api_key


def build_llm() -> LLM:
    """CrewAI 使用自己的 LLM 适配器，而不是手写请求或 LangChain 替身。"""
    return LLM(
        model=f"openai/{os.environ.get('MODEL_NAME', 'deepseek-chat')}",
        api_key=require_key(),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        temperature=0,
    )


def build_agents(llm: LLM) -> dict[str, Agent]:
    return {
        "pm": Agent(role="产品经理", goal="产出清晰、可验收的需求", backstory="擅长拆解用户问题", llm=llm),
        "backend": Agent(role="后端工程师", goal="设计可靠 API 契约", backstory="重视边界与错误处理", llm=llm),
        "tester": Agent(role="测试工程师", goal="发现交付风险", backstory="只认可可复现的验收证据", llm=llm),
    }


def build_tasks(agents: dict[str, Agent]) -> list[Task]:
    requirement = Task(
        description="为一个待办清单应用写出不超过 5 条的核心需求。",
        expected_output="中文需求清单，含至少一个边界条件。",
        agent=agents["pm"],
    )
    api_design = Task(
        description="根据需求清单设计创建和查询待办事项的 API。",
        expected_output="包含路径、方法、请求和响应字段的 API 说明。",
        agent=agents["backend"],
        context=[requirement],
    )
    # 两个有依赖的真实 Task 已足以演示 sequential 的产出传递，
    # 同时让课堂运行能在 30 秒交互时限内完成。
    return [requirement, api_design]


def main() -> None:
    llm = build_llm()
    agents = build_agents(llm)
    crew = Crew(agents=list(agents.values()), tasks=build_tasks(agents), process=Process.sequential)
    result = crew.kickoff()
    print("顺序团队交付完成：")
    print(result.raw)


if __name__ == "__main__":
    main()
