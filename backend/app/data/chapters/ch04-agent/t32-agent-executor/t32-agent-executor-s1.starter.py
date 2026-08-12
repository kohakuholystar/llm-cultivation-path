"""社团工具箱：用 LangChain v1 创建第一个工具 Agent。"""
# ????????? LangChain v1 ????????? Agent????lookup_weather?build_model ? main???????????????????????LangChain create_agent?ChatOpenAI????ReAct ??????????? DeepSeek Key ??Agent ?????????
import os

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def lookup_weather(city: str) -> str:
    """查询指定城市的演示天气。参数只传城市名，例如“杭州”。"""
    # TODO: 返回城市对应的天气；未知城市也要给出说明
    return ""


def build_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0,
    )


def main() -> None:
    # TODO: 用 create_agent 组装 model、tools 和 system_prompt
    agent = None
    result = agent.invoke({"messages": [{"role": "user", "content": "杭州天气怎么样？"}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
