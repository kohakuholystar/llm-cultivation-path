"""校园 AI 社 · s1：用真实 CrewAI Agent 定义团队角色。"""
import os
import sys

from crewai import Agent, LLM


def build_llm() -> LLM:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("请先在右上角 AI 配置填入 DeepSeek API Key，然后重新运行。")
        sys.exit(2)
    return LLM(model=f"openai/{os.environ.get('MODEL_NAME', 'deepseek-chat')}", api_key=api_key,
               base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"), temperature=0)


def build_heaven(llm: LLM) -> list[Agent]:
    return [
        Agent(role="产品经理", goal="把用户诉求翻译成可验收需求", backstory="最懂用户问题", llm=llm),
        Agent(role="后端工程师", goal="设计可靠 API", backstory="契约优先", llm=llm),
        Agent(role="前端工程师", goal="实现清晰界面", backstory="关注交互细节", llm=llm),
        Agent(role="测试工程师", goal="发现交付风险", backstory="只认可可复现证据", llm=llm),
    ]


def main() -> None:
    for agent in build_heaven(build_llm()):
        print(f"{agent.role}: {agent.goal}")


if __name__ == "__main__":
    main()
