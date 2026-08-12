"""校园 AI 社 · s5：真实 CrewAI 项目闭环，并把最终交付落盘。"""
import os
import sys
from pathlib import Path

from crewai import Agent, Crew, LLM, Process, Task


def build_llm() -> LLM:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("请先在右上角 AI 配置填入 DeepSeek API Key，然后重新运行。")
        sys.exit(2)
    return LLM(model=f"openai/{os.environ.get('MODEL_NAME', 'deepseek-chat')}", api_key=api_key,
               base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"), temperature=0)


def build_crew(llm: LLM) -> Crew:
    pm = Agent(role="产品经理", goal="把诉求变成可验收需求", backstory="关注用户价值", llm=llm)
    engineer = Agent(role="后端工程师", goal="设计可靠实现", backstory="坚持可维护 API", llm=llm)
    tester = Agent(role="测试工程师", goal="给出可执行验收", backstory="以失败路径为先", llm=llm)
    requirement = Task(description="为待办清单应用产出一份简要需求。", expected_output="三至五条需求。", agent=pm)
    api_design = Task(description="根据需求设计 REST API。", expected_output="含方法、路径、字段的方案。", agent=engineer, context=[requirement])
    acceptance = Task(description="为该 API 制定验收用例。", expected_output="至少三条带预期结果的用例。", agent=tester, context=[requirement, api_design])
    return Crew(agents=[pm, engineer, tester], tasks=[requirement, api_design, acceptance], process=Process.sequential)


def main() -> None:
    result = build_crew(build_llm()).kickoff()
    report_path = Path("校园 AI 社协作纪要.md")
    report_path.write_text("# 校园 AI 社协作纪要\n\n" + result.raw + "\n", encoding="utf-8")
    print(f"协作纪要已落盘：{report_path}")


if __name__ == "__main__":
    main()
