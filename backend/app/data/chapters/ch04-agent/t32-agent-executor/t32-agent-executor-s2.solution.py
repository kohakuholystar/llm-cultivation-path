"""社团工具箱：让模型根据工具 schema 填写多个参数。"""
import os

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def convert_temperature(value: float, target_unit: str) -> str:
    """把摄氏温度转换为 C 或 F。value 是摄氏数值，target_unit 只能是 C 或 F。"""
    if target_unit.upper() == "C":
        return f"{value:g} °C"
    if target_unit.upper() == "F":
        return f"{value * 9 / 5 + 32:g} °F"
    return "参数错误：target_unit 只能是 C 或 F"


def main() -> None:
    model = ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["OPENAI_API_KEY"], temperature=0,
    )
    agent = create_agent(
        model=model, tools=[convert_temperature],
        system_prompt="你是单位助手。温度换算必须调用工具，不要猜测工具结果。",
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "把 20 摄氏度换成华氏度"}]},
        config={"recursion_limit": 8},
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
