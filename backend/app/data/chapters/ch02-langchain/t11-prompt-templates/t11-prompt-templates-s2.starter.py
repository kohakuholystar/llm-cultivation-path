"""黑糖资料室 · 提示词模板工程 · s2：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：通过 few-shot 示例约束模型的输出格式。
# - 补写：补写单条示例、few-shot 块和主模板。
# - 关键函数/类（入参 → 出参）：`build_example_prompt()` 定义示例消息；`build_fewshot_block(examples)` 构造示例块；`build_forge_prompt(examples)` 返回组合模板。
# - 技术栈：LangChain Core、Few-shot Prompting。
# - 前置条件：本步只渲染模板；示例字段必须与模板占位符一致。
# - 可观察结果：渲染结果包含示例和当前请求。

from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)
from langchain_core.messages import BaseMessage

# 制作示例库:每条是 (制作需求, 标准交付卡) 的对照。
# 示例不在多而在精——每条都会占 token,风格必须统一,它就是你要的标准。
FORGE_EXAMPLES = [
    {
        "request": "轻巧短视频脚本,适合贴身移动端展示",
        "recipe": "《鱼肠》双刃短视频脚本|长一尺二寸|重一斤|优化细节:冷色滤镜|特性:藏锋",
    },
    {
        "request": "马上用的长刀,要劈砍有力",
        "recipe": "《破阵》环首长刀|长四尺|重八斤|优化细节:桐油|特性:势沉",
    },
    {
        "request": "文人活动主视觉,以礼为主不尚杀伐",
        "recipe": "《君子》七星内容方案|长三尺三|重二斤|优化细节:山泉|特性:仪礼",
    },
]


def build_example_prompt() -> ChatPromptTemplate:
    """定义单条示例的呈现格式:一条 human 需求 + 一条 ai 交付卡。

    示例的"答案"必须用 ai 角色——等于告诉模型"你以前就是这么答的"。
    """
    # TODO: 返回单条示例的呈现模板:一条 human 需求 + 一条 ai 交付卡
    # 提示: ChatPromptTemplate.from_messages(
    #       [("human", "{request}"), ("ai", "{recipe}")])
    raise NotImplementedError("build_example_prompt 尚未实现:请按 TODO 提示定义示例格式")


def build_fewshot_block(examples: list[dict]) -> FewShotChatMessagePromptTemplate:
    """把示例库按 example_prompt 逐条渲染,包成一个可插入的消息块。"""
    if not examples:
        raise ValueError("few-shot 示例库不能为空")
    # TODO: 用 FewShotChatMessagePromptTemplate 把示例库包成消息块
    # 提示: FewShotChatMessagePromptTemplate(
    #       examples=examples, example_prompt=build_example_prompt())
    raise NotImplementedError("build_fewshot_block 尚未实现:请按 TODO 提示构建示例块")


def build_forge_prompt(examples: list[dict]) -> ChatPromptTemplate:
    """主模板 = system 人设 + few-shot 示例块 + 当前需求。"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", "你是提示词工作台的提示词负责人,出身团队「{sect}」。"
                       "请模仿示例的格式开输出模板。"),
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
        {"sect": "素材组", "request": "双手长篇方案,主材活动素材,要能劈开城门"},
    )
    # 消息数 = 1 条 system + 2×3 条示例 + 1 条当前需求 = 8
    print(f"渲染出 {len(messages)} 条消息:")
    show_messages(messages)


if __name__ == "__main__":
    main()
