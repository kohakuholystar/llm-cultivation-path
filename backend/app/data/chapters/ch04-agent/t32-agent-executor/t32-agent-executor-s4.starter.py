"""社团工具箱：观察 Agent 状态并设置执行上限。"""
# ?????????? Agent ?????????????word_count ???????????????????????????messages?recursion_limit????t32-s3????????????????????????
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
    # TODO: 调用 Agent，并通过 config={"recursion_limit": 8} 约束本次执行
    result = agent.invoke({"messages": [{"role": "user", "content": "请计算 'agent state has messages' 有几个英文单词"}]})
    # TODO: 遍历 result["messages"]，打印每条消息的 type 与 content
    print(result)


if __name__ == "__main__":
    main()
