"""黑糖资料室 · 项目咨询路由 · s1：用 LangChain 完成可验证的学习任务。"""
import os
import sys

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

MOCK_LLM = os.environ.get("MOCK_LLM") == "1"

# 无 Key 且未开 MOCK 时给出引导并优雅退出,不让学习者面对 traceback
if not MOCK_LLM and not os.environ.get("OPENAI_API_KEY"):
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

# 黑糖资料室的四种来意:制作 / 撰写文案 / 质量评审 / 闲聊
INTENT_OPTIONS = ("forge", "inscribe", "appraise", "chat")


def build_llm(mock_replies=None) -> BaseChatModel:
    """模型工厂:MOCK 时返回按剧本作答的假模型,否则接 DeepSeek。"""
    if MOCK_LLM:
        return FakeListChatModel(responses=mock_replies or ["chat"])
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0,  # 分类任务要稳,不要发挥
    )


def build_classifier_chain():
    """意图分类链:提示词 → 模型 → 字符串解析,出口类型就是 str。"""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你是提示词工作台的接待。判断客人来意,只回答一个词:"
                       "forge(内容制作)、inscribe(撰写文案)、appraise(质量评审)、chat(闲聊)。"),
            ("human", "{request}"),
        ]
    )
    # 三段式:模板限定候选词 → 模型判定 → 解析器把 AIMessage 剥成纯字符串
    return prompt | build_llm(["forge", "inscribe", "chat"]) | StrOutputParser()


def normalize_intent(raw: str) -> str:
    """清洗模型输出:包含即命中,不中归 chat,脏值绝流不进下游分支。"""
    text = raw.strip().lower()
    for intent in INTENT_OPTIONS:
        if intent in text:
            return intent
    return "chat"  # 模型不守规矩时的兜底


def main() -> None:
    """拿三位咨询者的开场白试链。"""
    chain = build_classifier_chain()
    requests = [
        "我想做一份重点突出的内容方案",
        "给我的活动主视觉题一句文案",
        "今天天气怎么样",
    ]
    print("== 提示词工作台 · 问明来意 ==")
    for req in requests:
        intent = normalize_intent(chain.invoke({"request": req}))
        print(f"  客人:「{req}」→ 来意:{intent}")


if __name__ == "__main__":
    main()
