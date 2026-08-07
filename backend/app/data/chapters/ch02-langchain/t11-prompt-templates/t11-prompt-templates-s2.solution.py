"""铸剑台 · 模板工程 第 2 步:Few-shot 示例模板。

零样本(只下指令)时模型输出格式飘忽;给几条"需求→标准剑谱"示例,
模型靠上下文学习自动模仿示例的字段与风格。
在第 1 步基础上演进:system 人设 + few-shot 示例块 + 当前需求。
"""

from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)
from langchain_core.messages import BaseMessage

# 铸剑示例库:每条是 (铸剑需求, 标准剑谱) 的对照。
# 示例不在多而在精——每条都会占 token,风格必须统一,它就是你要的标准。
FORGE_EXAMPLES = [
    {
        "request": "轻巧短剑,适合贴身暗卫",
        "recipe": "《鱼肠》双刃短剑|长一尺二寸|重一斤|淬火:寒潭水|特性:藏锋",
    },
    {
        "request": "马上用的长刀,要劈砍有力",
        "recipe": "《破阵》环首长刀|长四尺|重八斤|淬火:桐油|特性:势沉",
    },
    {
        "request": "文人佩剑,以礼为主不尚杀伐",
        "recipe": "《君子》七星宝剑|长三尺三|重二斤|淬火:山泉|特性:仪礼",
    },
]


def build_example_prompt() -> ChatPromptTemplate:
    """定义单条示例的呈现格式:一条 human 需求 + 一条 ai 剑谱。

    示例的"答案"必须用 ai 角色——等于告诉模型"你以前就是这么答的"。
    """
    return ChatPromptTemplate.from_messages(
        [("human", "{request}"), ("ai", "{recipe}")]
    )


def build_fewshot_block(examples: list[dict]) -> FewShotChatMessagePromptTemplate:
    """把示例库按 example_prompt 逐条渲染,包成一个可插入的消息块。"""
    if not examples:
        raise ValueError("few-shot 示例库不能为空")
    return FewShotChatMessagePromptTemplate(
        examples=examples,
        example_prompt=build_example_prompt(),
    )


def build_forge_prompt(examples: list[dict]) -> ChatPromptTemplate:
    """主模板 = system 人设 + few-shot 示例块 + 当前需求。"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", "你是铸剑台的总铸剑师,出身门派「{sect}」。"
                       "请模仿示例的格式开剑谱。"),
            build_fewshot_block(examples),  # 示例块作为整体插入此处
            ("human", "{request}"),
        ]
    )


def render_messages(
    prompt: ChatPromptTemplate, variables: dict
) -> list[BaseMessage]:
    """渲染模板为消息列表;缺参时给出中文提示。"""
    try:
        return prompt.invoke(variables).to_messages()
    except KeyError as exc:
        raise KeyError(f"模板渲染失败,缺少变量: {exc.args[0]}") from exc


def show_messages(messages: list[BaseMessage]) -> None:
    """带序号打印每条消息:观察示例渲染成真实的 human/ai 交替。"""
    for i, msg in enumerate(messages, 1):
        print(f"{i}. [{msg.type}] {msg.content}")


def main() -> None:
    prompt = build_forge_prompt(FORGE_EXAMPLES)

    # 示例自带的变量(request/recipe)由示例库提供,不构成模板的入参
    print("模板声明的变量:", sorted(prompt.input_variables))

    messages = render_messages(
        prompt,
        {"sect": "玄铁阁", "request": "双手重剑,主材天外陨铁,要能劈开城门"},
    )
    # 消息数 = 1 条 system + 2×3 条示例 + 1 条当前需求 = 8
    print(f"渲染出 {len(messages)} 条消息:")
    show_messages(messages)


if __name__ == "__main__":
    main()
