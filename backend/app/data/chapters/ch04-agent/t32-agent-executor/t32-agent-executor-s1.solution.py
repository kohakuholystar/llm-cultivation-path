"""社团工具箱：LangChain v1 的第一个工具 Agent。"""
import os

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def lookup_weather(city: str) -> str:
    """查询指定城市的演示天气。参数只传城市名，例如“杭州”。"""
    return {"杭州": "晴，26°C", "北京": "多云，18°C"}.get(city, f"没有 {city} 的天气数据")


def build_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0,
    )


def main() -> None:
    agent = create_agent(
        model=build_model(),
        tools=[lookup_weather],
        system_prompt="你是社团工具箱。需要天气时必须调用 lookup_weather，再用中文简洁回答。",
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "杭州天气怎么样？"}]},
        config={"recursion_limit": 8},
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
