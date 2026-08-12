"""社团工具箱：工具失败也要返回可行动的信息。"""
import os

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def divide(dividend: float, divisor: float) -> str:
    """计算 dividend 除以 divisor。除数为 0 时返回可解释的错误，而不是抛出异常。"""
    if divisor == 0:
        return "计算失败：除数不能为 0。请向用户说明并询问新的除数。"
    return str(dividend / divisor)


def main() -> None:
    model = ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"), base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"), api_key=os.environ["OPENAI_API_KEY"], temperature=0)
    agent = create_agent(model=model, tools=[divide], system_prompt="你是计算助手。调用工具失败时解释原因，不要编造数值。")
    result = agent.invoke({"messages": [{"role": "user", "content": "计算 10 除以 0"}]}, config={"recursion_limit": 8})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
