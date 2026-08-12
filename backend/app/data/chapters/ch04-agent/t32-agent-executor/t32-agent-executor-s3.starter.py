"""社团工具箱：把工具失败变成可读的结果。"""
# ???????????????????????divide ????????????????????????????????@tool?????????t32-s2???????????? Agent ?????
import os

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def divide(dividend: float, divisor: float) -> str:
    """计算 dividend 除以 divisor。除数为 0 时返回可解释的错误，而不是抛出异常。"""
    # TODO: 对 divisor == 0 返回中文错误；否则返回除法结果
    return ""


def main() -> None:
    model = ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"), base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"), api_key=os.environ["OPENAI_API_KEY"], temperature=0)
    # TODO: create_agent 的 system_prompt 要求失败时不编造结果
    agent = None
    result = agent.invoke({"messages": [{"role": "user", "content": "计算 10 除以 0"}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
