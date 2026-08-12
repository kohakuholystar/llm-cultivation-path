"""社团工具箱：危险工具先暂停，再由人类决定。"""
# ????????????????????????send_notice ? interrupt/resume ?????????????????????????????LangGraph InMemorySaver?Command????t32-s4????????????????????
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
    # TODO: 用 InMemorySaver、interrupt_before=["tools"] 创建可暂停的 Agent
    agent = None
    config = {"configurable": {"thread_id": "notice-demo"}, "recursion_limit": 8}
    paused = agent.invoke({"messages": [{"role": "user", "content": "给小林发送：会议改到三点"}]}, config=config)
    print("待人工确认的工具调用：", paused["messages"][-1].tool_calls)
    # TODO: 用户输入 y 时，用 Command(resume={}) 继续；否则直接取消


if __name__ == "__main__":
    main()
