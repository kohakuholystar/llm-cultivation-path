"""校园 AI 社 · s4：CrewAI hierarchical 的真实总管编排。"""
import os
import sys

from crewai import Agent, Crew, LLM, Process, Task


def build_llm() -> LLM:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("请先在右上角 AI 配置填入 DeepSeek API Key，然后重新运行。")
        sys.exit(2)
    return LLM(model=f"openai/{os.environ.get('MODEL_NAME', 'deepseek-chat')}", api_key=api_key,
               base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"), temperature=0)


def main() -> None:
    llm = build_llm()
    reviewer = Agent(
        role="接口评审员",
        goal="给出一个可执行的最小安全约束",
        backstory="擅长把模糊需求压缩为可验证的接口规则",
        llm=llm,
    )
    tasks = [
        Task(
            description="为登录接口给出 1 条最小安全约束；只输出一条完整中文句子。",
            expected_output="一条不超过 30 字的中文安全约束。",
            agent=reviewer,
        ),
    ]
    # manager_llm 是 CrewAI 官方 hierarchical 流程的总管模型，不再自造 Crew 类。
    crew = Crew(agents=[reviewer], tasks=tasks, process=Process.hierarchical, manager_llm=llm)
    result = crew.kickoff()
    print("层级团队交付完成：")
    print(result.raw)


if __name__ == "__main__":
    main()
