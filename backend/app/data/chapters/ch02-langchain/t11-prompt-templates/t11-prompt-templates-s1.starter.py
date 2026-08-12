"""黑糖资料室 · 提示词模板工程 · s1：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：把提示词写成显式变量的消息模板，而非字符串拼接。
# - 补写：补写 `build_forge_prompt`。
# - 关键函数/类（入参 → 出参）：`build_forge_prompt() -> ChatPromptTemplate` 返回 system/human 模板；`render_messages(prompt, variables: dict)` 渲染消息。
# - 技术栈：LangChain Core、`ChatPromptTemplate`、`BaseMessage`。
# - 前置条件：本步只渲染模板，不需要联网或 API Key。
# - 可观察结果：打印包含角色与内容的消息列表。

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage


def build_forge_prompt() -> ChatPromptTemplate:
    """构建黑糖资料室主模板:system 锁定内容设计师人设,human 接收制作需求。"""
    # TODO: 用 ChatPromptTemplate.from_messages([...]) 返回模板,含两条消息
    # 提示: ("system", "你是黑糖资料室的项目主理人,出身社团「{sect}」。"
    #        "你只回答制作相关问题,其余话题一律回绝。")
    #       ("human", "我要制作一份{sword_type},主素材是{material},请给出制作要点。")
    raise NotImplementedError("build_forge_prompt 尚未实现:请按 TODO 提示构建主模板")


def render_messages(
    prompt: ChatPromptTemplate, variables: dict
) -> list[BaseMessage]:
    """把变量注入模板,渲染成消息列表;缺参时给出中文提示。"""
    try:
        return prompt.invoke(variables).to_messages()
    except KeyError as exc:
        # KeyError.args[0] 就是缺失的变量名——报错暴露在渲染期,是好事
        raise KeyError(f"模板渲染失败,缺少变量: {exc.args[0]}") from exc


def show_messages(messages: list[BaseMessage]) -> None:
    """逐条打印消息角色与内容——这就是将来发给模型的样子。"""
    for msg in messages:
        print(f"[{msg.type}] {msg.content}")


def main() -> None:
    prompt = build_forge_prompt()

    # input_variables 是模板自动解析出的"函数签名",可用来核对调用参数
    print("模板声明的变量:", sorted(prompt.input_variables))

    messages = render_messages(
        prompt,
        {"sect": "素材组", "sword_type": "双手长篇方案", "material": "活动素材"},
    )
    show_messages(messages)

    # 换一组变量,同一份模板渲染出完全不同的提示词——模板即数据
    print("--- 换一批内容制作需求 ---")
    messages2 = render_messages(
        prompt,
        {"sect": "视觉设计组", "sword_type": "竖版海报", "material": "精钢"},
    )
    show_messages(messages2)


if __name__ == "__main__":
    main()
