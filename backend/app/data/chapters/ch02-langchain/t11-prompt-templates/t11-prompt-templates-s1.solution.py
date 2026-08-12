"""黑糖资料室 · 提示词模板工程 · s1：用 LangChain 完成可验证的学习任务。"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage


def build_forge_prompt() -> ChatPromptTemplate:
    """构建黑糖资料室主模板:system 锁定内容设计师人设,human 接收制作需求。"""
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                # 人设与行为边界放 system,模型对 system 指令服从度更高
                "你是提示词工作台的提示词负责人,出身团队「{sect}」。"
                "你只回答内容策划问题,其余话题一律回绝。",
            ),
            (
                "human",
                # 当前需求放 human:{xxx} 即模板变量,渲染时被替换
                "我要制作一份{sword_type},主素材是{material},请给出制作要点。",
            ),
        ]
    )


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
