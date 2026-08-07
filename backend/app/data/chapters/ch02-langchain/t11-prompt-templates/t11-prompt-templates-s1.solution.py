"""铸剑台 · 模板工程 第 1 步:ChatPromptTemplate 基础。

把铸剑配方从"字符串拼接"升级为"显式声明变量的模板",
实现提示词内容与代码分离。本任务全程只渲染 prompt,不调用模型。
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage


def build_forge_prompt() -> ChatPromptTemplate:
    """构建铸剑台主模板:system 锁定铸剑师人设,human 接收铸剑需求。"""
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                # 人设与行为边界放 system,模型对 system 指令服从度更高
                "你是铸剑台的总铸剑师,出身门派「{sect}」。"
                "你只回答铸剑相关问题,其余话题一律回绝。",
            ),
            (
                "human",
                # 当前需求放 human:{xxx} 即模板变量,渲染时被替换
                "我要铸一柄{sword_type},主材是{material},请给出锻造要点。",
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
        {"sect": "玄铁阁", "sword_type": "双手重剑", "material": "天外陨铁"},
    )
    show_messages(messages)

    # 换一组变量,同一份模板渲染出完全不同的提示词——模板即数据
    print("--- 换一批铸剑需求 ---")
    messages2 = render_messages(
        prompt,
        {"sect": "百花谷", "sword_type": "柳叶细剑", "material": "精钢"},
    )
    show_messages(messages2)


if __name__ == "__main__":
    main()
