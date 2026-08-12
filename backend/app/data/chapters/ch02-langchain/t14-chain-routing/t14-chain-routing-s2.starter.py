"""黑糖资料室 · 项目咨询路由 · s2：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：基于分类结果，用 `RunnableBranch` 将请求送到对应处理链。
# - 补写：补写三条业务链与路由器。
# - 关键函数/类（入参 → 出参）：`build_*_chain()` 返回具体处理链；`build_router()` 返回按意图选择分支的路由器。
# - 技术栈：LangChain Core、`RunnableBranch`、`RunnablePassthrough.assign`。
# - 前置条件：真实调用需右上角 DeepSeek API Key。
# - 可观察结果：输入请求经过分类后进入相应的项目咨询分支。
import os
import sys

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableBranch, RunnablePassthrough
from langchain_openai import ChatOpenAI

MOCK_LLM = os.environ.get("MOCK_LLM") == "1"

# 无 Key 且未开 MOCK 时给出引导并优雅退出
if not MOCK_LLM and not os.environ.get("OPENAI_API_KEY"):
    print("[提示词工作台] 未检测到 OPENAI_API_KEY。")
    print("请先在右上角 AI 配置填入 DeepSeek API Key,然后重新运行。")
    sys.exit(0)

INTENT_OPTIONS = ("forge", "inscribe", "appraise", "chat")


def build_llm(mock_replies=None) -> BaseChatModel:
    """模型工厂:MOCK 时返回按剧本作答的假模型,否则接 DeepSeek。"""
    if MOCK_LLM:
        return FakeListChatModel(responses=mock_replies or ["chat"])
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["OPENAI_API_KEY"],
        temperature=0,
    )


def build_classifier_chain():
    """意图分类链(s1 的件):出口是原始判定文本。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是提示词工作台的接待。判断客人来意,只回答一个词:"
                   "forge(内容制作)、inscribe(撰写文案)、appraise(质量评审)、chat(闲聊)。"),
        ("human", "{request}"),
    ])
    return prompt | build_llm(["forge", "inscribe", "appraise", "chat"]) | StrOutputParser()


def normalize_intent(raw: str) -> str:
    """清洗模型输出:包含即命中,不中归 chat。"""
    text = raw.strip().lower()
    for intent in INTENT_OPTIONS:
        if intent in text:
            return intent
    return "chat"


def build_forge_chain():
    """制作组:散文答复制作方案。"""
    prompt = ChatPromptTemplate.from_messages([("system", "你是内容策划助手,三句话内给出内容制作方案。"), ("human", "{request}")])
    return prompt | build_llm(["建议以冷色调素材为基础,补充标题层级与留白,再完成版式检查。"]) | StrOutputParser()


def build_inscribe_chain():
    """文案组:为内容方案撰写文案。"""
    prompt = ChatPromptTemplate.from_messages([("system", "你是文案师,题一句四言或七言文案。"), ("human", "{request}")])
    return prompt | build_llm(["让创意被看见,今日把示君。"]) | StrOutputParser()


def build_chat_chain():
    """咨询台:闲聊兜底,也是路由器的默认分支。"""
    prompt = ChatPromptTemplate.from_messages([("system", "你是提示词工作台掌柜,陪客人闲聊,谈吐风趣。"), ("human", "{request}")])
    return prompt | build_llm(["坐,处理器上正温着茶,慢慢聊。"]) | StrOutputParser()


def build_router():
    """路由器:assign 先给字典追加 intent 字段,RunnableBranch 再按序分流。"""
    # TODO: 把「判定 + 清洗」焊成 classify,再用 assign + RunnableBranch 组装路由器
    # 提示: classify = build_classifier_chain() | normalize_intent  # 函数接在 | 后自动包装成 Runnable
    #       return RunnablePassthrough.assign(intent=classify) | RunnableBranch(
    #           (lambda x: x["intent"] == "forge", build_forge_chain()),
    #           (lambda x: x["intent"] == "inscribe", build_inscribe_chain()),
    #           build_chat_chain())  # 默认分支:其余来意(含 appraise)一律奉茶,必须存在
    raise NotImplementedError("build_router 尚未实现:请按 TODO 提示组装三路分流路由器")


def main() -> None:
    """四位咨询者轮番上门,观察分流结果。"""
    router = build_router()
    guests = ["我要制作一份活动主视觉", "为这份方案写一句短文案", "帮我鉴赏这份旧版设计", "今天天气如何"]
    print("== 提示词工作台 · 三路分流 ==")
    for g in guests:
        reply = router.invoke({"request": g})
        print(f"客人:「{g}」\n  接待:{reply}")


if __name__ == "__main__":
    main()
