"""社团工具箱：在真正执行工具前暂停，交给人类确认。"""
import os

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command


@tool
def send_notice(recipient: str, text: str) -> str:
    """向 recipient 发送 text。它是有外部影响的演示工具，必须人工确认后才能执行。"""
    return f"已向 {recipient} 发送：{text}"


def main() -> None:
    model = ChatOpenAI(model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"), base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"), api_key=os.environ["OPENAI_API_KEY"], temperature=0)
    agent = create_agent(
        model=model, tools=[send_notice],
        system_prompt="你是通知助手。发送通知前说明对象和内容。",
        checkpointer=InMemorySaver(), interrupt_before=["tools"],
    )
    config = {"configurable": {"thread_id": "notice-demo"}, "recursion_limit": 8}
    paused = agent.invoke({"messages": [{"role": "user", "content": "给小林发送：会议改到三点"}]}, config=config)
    proposal = paused["messages"][-1]
    print("待人工确认的工具调用：", proposal.tool_calls)
    approval = input("确认执行？[y/N] ") if sys.stdin.isatty() else "n"
    if approval.strip().lower() != "y":
        print("已取消；工具没有执行。")
        return
    result = agent.invoke(Command(resume={}), config=config)
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
