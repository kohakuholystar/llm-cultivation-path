"""校园 AI 社 · s2：用真实 CrewAI Task 表达依赖关系。"""
import os
import sys

from crewai import Agent, LLM, Task


def build_llm() -> LLM:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("请先在右上角 AI 配置填入 DeepSeek API Key，然后重新运行。")
        sys.exit(2)
    return LLM(model=f"openai/{os.environ.get('MODEL_NAME', 'deepseek-chat')}", api_key=api_key,
               base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"), temperature=0)


def build_plan(llm: LLM) -> list[Task]:
    pm = Agent(role="产品经理", goal="写需求", backstory="关注用户", llm=llm)
    engineer = Agent(role="后端工程师", goal="设计 API", backstory="契约优先", llm=llm)
    frontend = Agent(role="前端工程师", goal="实现界面", backstory="交互清晰", llm=llm)
    tester = Agent(role="测试工程师", goal="验收交付", backstory="可复现验证", llm=llm)
    requirement = Task(description="列出待办应用的核心需求。", expected_output="三至五条需求。", agent=pm)
    api_design = Task(description="根据需求设计 API。", expected_output="接口契约。", agent=engineer, context=[requirement])
    ui_design = Task(description="根据 API 设计待办界面交互。", expected_output="界面交互说明。", agent=frontend, context=[api_design])
    acceptance = Task(description="根据前置产出编写测试验收清单。", expected_output="可执行验收用例。", agent=tester, context=[requirement, api_design, ui_design])
    return [requirement, api_design, ui_design, acceptance]


def main() -> None:
    stages = ["需求分析", "API 设计", "前端开发", "测试验收"]
    for stage, task in zip(stages, build_plan(build_llm())):
        print(f"{stage}: {task.description}")


if __name__ == "__main__":
    main()
