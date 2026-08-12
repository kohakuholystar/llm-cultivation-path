"""社团工具箱：认识工具参数 schema。"""
# ?????????????? schema????convert_temperature ? Agent ???????????????????????????@tool?LangChain????t32-s1???????????????????????
import os

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def convert_temperature(value: float, target_unit: str) -> str:
    """把摄氏温度转换为 C 或 F。value 是摄氏数值，target_unit 只能是 C 或 F。"""
    # TODO: C 原样返回，F 用 value * 9 / 5 + 32；其他单位返回明确错误
    return ""


def main() -> None:
    model = ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"), base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"), api_key=os.environ["OPENAI_API_KEY"], temperature=0)
    # TODO: 创建只允许使用 convert_temperature 的 Agent
    agent = None
    result = agent.invoke({"messages": [{"role": "user", "content": "把 20 摄氏度换成华氏度"}]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
