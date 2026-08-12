"""社团工具箱：给 Agent 的状态图设置执行边界。"""
import os

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


@tool
def word_count(text: str) -> str:
    """返回文本按空白分隔后的单词数。"""
    return str(len(text.split()))


def main() -> None:
    model = ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"), base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"), api_key=os.environ["OPENAI_API_KEY"], temperature=0)
    agent = create_agent(model=model, tools=[word_count], system_prompt="需要计数时调用 word_count。")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "请计算 'agent state has messages' 有几个英文单词"}]},
        # v1 Agent 是状态图；recursion_limit 是一次图执行可走的最大节点步数。
        config={"recursion_limit": 8},
    )
    for message in result["messages"]:
        print(f"{message.type}: {message.content}")


if __name__ == "__main__":
    main()
