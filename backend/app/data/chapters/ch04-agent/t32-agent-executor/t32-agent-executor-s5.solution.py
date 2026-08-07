"""百宝囊 · 第5关: 天眼通 verbose 与轨迹回放
verbose=True 看实时推理流; return_intermediate_steps=True 拿结构化轨迹做审计。
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


@tool
def duliangheng(query: str) -> str:
    """度量衡: 长度换算。输入格式 "数值 源单位 目标单位", 如 "3 里 米", 支持 里/丈/尺/米。"""

    to_meter = {"里": 500.0, "丈": 10 / 3, "尺": 1 / 3, "米": 1.0}
    try:
        value_s, src, dst = query.split()
        # 先折成米, 再折成目标单位
        return f"{query} = {float(value_s) * to_meter[src] / to_meter[dst]:g} {dst}"
    except (ValueError, KeyError) as exc:
        return f"换算失败({exc}), 请用格式: 数值 源单位 目标单位"


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


def build_executor(tools: list, script: list) -> AgentExecutor:
    """带天眼通的执行官: verbose 看直播, intermediate_steps 留底回放。"""

    agent = create_react_agent(build_llm(script), tools, REACT_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=5,
        handle_parsing_errors=True,
        verbose=True,  # 直播: 每轮 Thought/Action/Observation 实时打印
        return_intermediate_steps=True,  # 留底: 轨迹收进结果的 intermediate_steps 键
    )


def print_trajectory(result: dict) -> None:
    """回放结构化轨迹: 逐步列出 (宝器, 输入, 回报)。"""

    steps = result.get("intermediate_steps", [])
    print(f"\n== 行动轨迹回放(共 {len(steps)} 步)==")
    for i, (action, observation) in enumerate(steps, 1):
        print(f"  第{i}步 宝器[{action.tool}] 输入={action.tool_input!r} 回报={observation}")


def main() -> None:
    tools = [shenji_suanpan, qianli_yan, duliangheng]
    executor = build_executor(tools, MOCK_SCRIPT)
    print("== 百宝囊 · 天眼通调试 ==")
    result = executor.invoke({"input": "3*(4+5) 等于多少?"})
    print("\n最终答复:", result["output"])
    print_trajectory(result)


if __name__ == "__main__":
    main()
