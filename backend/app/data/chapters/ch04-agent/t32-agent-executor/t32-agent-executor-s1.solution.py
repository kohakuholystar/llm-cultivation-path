"""百宝囊 · 第1关: 铸造宝器, 组装 Agent
用 @tool 打造工具箱, create_react_agent 把模型/工具/提示词拧成 Agent。
"""
import os
import sys

from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

MOCK = os.environ.get("MOCK_LLM") == "1"

# 没有 Key 就给出引导并优雅退出, 不让学习者面对 traceback
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("[百宝囊] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)


def build_llm(script: list) -> BaseChatModel:
    """联网模式返回 DeepSeek 客户端; MOCK 模式返回循环念台词的假模型。"""

    if MOCK:
        return FakeListChatModel(responses=script)  # 官方假模型, 台词念完自动从头再来
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0,  # Agent 场景要稳定, 不要发散
    )


@tool
def shenji_suanpan(expression: str) -> str:
    """神机算盘: 计算数学表达式, 输入如 "3 * (4 + 5)"。"""

    try:
        # 关死 builtins 只许算术, 防止表达式注入
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as exc:
        # 报错信息也是给模型看的"回报", 写清楚它才知道怎么改
        return f"算盘打不出: {exc}"


@tool
def qianli_yan(city: str) -> str:
    """千里眼: 查询城市天气, 输入城市名, 如 "杭州"。"""

    observed = {"杭州": "晴 26°C", "北京": "多云 18°C", "长安": "小雨 15°C"}
    return observed.get(city, f"{city}: 晴 22°C(百宝囊内置观测)")


REACT_PROMPT = ChatPromptTemplate.from_template(
    "你是「百宝囊」, 一座会思考的工具箱, 回答尽量借助宝器(工具)。\n"
    "可用宝器:\n{tools}\n宝器名录(只能从中选): {tool_names}\n"
    "严格按此格式行动(可重复多轮):\n"
    "Thought: 你的思考\nAction: 宝器名\nAction Input: 给宝器的输入\nObservation: 宝器的回报\n"
    "Thought: 我现在知道最终答案了\nFinal Answer: 给用户的最终答复\n"
    "问题: {input}\n{agent_scratchpad}"
)


# 剧本: 第一轮请算盘, 第二轮给最终答案(FakeListChatModel 循环念台词)
MOCK_SCRIPT = [
    "Thought: 这是算术题, 请神机算盘\nAction: shenji_suanpan\nAction Input: 3*(4+5)",
    "Thought: 我现在知道最终答案了\nFinal Answer: 3*(4+5) = 27",
]


def main() -> None:
    tools = [shenji_suanpan, qianli_yan]
    print("== 百宝囊 · 开囊清点 ==")
    for t in tools:
        print(f"  宝器[{t.name}] {t.description.split(':', 1)[0]}")

    # 三件套合体: 模型 + 工具 + ReAct 提示词 -> Agent(一个 Runnable)
    agent = create_react_agent(build_llm(MOCK_SCRIPT), tools, REACT_PROMPT)
    executor = AgentExecutor(agent=agent, tools=tools)
    ans = executor.invoke({"input": "3*(4+5) 等于多少?"})
    print("百宝囊答复:", ans["output"])


if __name__ == "__main__":
    main()
