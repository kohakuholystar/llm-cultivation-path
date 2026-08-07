"""铸剑台 · s1:问明来意 —— 意图分类链

铸剑台开张,客人进门说什么的都有:铸剑的、题字的、鉴宝的、纯聊天的。
接待第一步是"问明来意":用一条分类链把自然语言请求归到固定意图,
后续步骤才能按意图分流。这是章项目收官任务的第一块件。
"""
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
    print("[铸剑台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

# 铸剑台的四种来意:铸剑 / 题铭文 / 鉴剑 / 闲聊
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
    # TODO: 用 | 把 prompt、build_llm(["forge", "inscribe", "chat"])、StrOutputParser() 串成链并 return
    # 提示: prompt = ChatPromptTemplate.from_messages([
    #           ("system", "你是铸剑台的接待。判断客人来意,只回答一个词:"
    #                      "forge(铸剑)、inscribe(题铭文)、appraise(鉴剑)、chat(闲聊)。"),
    #           ("human", "{request}"),
    #       ])
    #       三段式:模板限定候选词 → 模型判定 → 解析器把 AIMessage 剥成纯字符串;
    #       MOCK 剧本依次判出 forge / inscribe / chat
    raise NotImplementedError("build_classifier_chain 尚未实现:请按 TODO 提示组装意图分类链")


def normalize_intent(raw: str) -> str:
    """清洗模型输出:包含即命中,不中归 chat,脏值绝流不进下游分支。"""
    # TODO: 清洗并归一到标准意图词,脏值绝流不进下游分支
    # 提示: text = raw.strip().lower();遍历 INTENT_OPTIONS,若 intent 出现在 text 中就 return intent;
    #       循环结束仍无命中则 return "chat" 兜底(模型不守规矩时的兜底)
    raise NotImplementedError("normalize_intent 尚未实现:请按 TODO 提示清洗模型输出")


def main() -> None:
    """拿三位客人的开场白试链。"""
    chain = build_classifier_chain()
    requests = [
        "我想铸一柄削铁如泥的宝剑",
        "给我的佩剑题一句铭文",
        "今天天气怎么样",
    ]
    print("== 铸剑台 · 问明来意 ==")
    for req in requests:
        intent = normalize_intent(chain.invoke({"request": req}))
        print(f"  客人:「{req}」→ 来意:{intent}")


if __name__ == "__main__":
    main()
