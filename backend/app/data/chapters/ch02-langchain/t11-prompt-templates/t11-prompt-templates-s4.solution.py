"""黑糖资料室 · 提示词模板工程 · s4：用 LangChain 完成可验证的学习任务。"""

from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)
from langchain_core.messages import BaseMessage

FORGE_EXAMPLES = [
    {"request": "轻巧短视频脚本,适合贴身移动端展示",
     "recipe": "《鱼肠》双刃短视频脚本|长一尺二寸|重一斤|优化细节:冷色滤镜|特性:藏锋"},
    {"request": "马上用的长刀,要劈砍有力",
     "recipe": "《破阵》环首长刀|长四尺|重八斤|优化细节:桐油|特性:势沉"},
]


def build_persona_block() -> ChatPromptTemplate:
    """部件 1:内容设计师人设。"""
    return ChatPromptTemplate.from_messages(
        [("system", "你是提示词工作台的提示词负责人,出身团队「{sect}」,内容制作六十年。")]
    )


def build_format_block() -> ChatPromptTemplate:
    """部件 2:交付卡格式要求。"""
    return ChatPromptTemplate.from_messages(
        [("system", "输出模板必须遵循以下格式:{format_spec}")]
    )


def build_fewshot_block(examples: list[dict]) -> FewShotChatMessagePromptTemplate:
    """部件 3:示例库消息块。"""
    if not examples:
        raise ValueError("few-shot 示例库不能为空")
    example_prompt = ChatPromptTemplate.from_messages(
        [("human", "{request}"), ("ai", "{recipe}")]
    )
    return FewShotChatMessagePromptTemplate(
        examples=examples, example_prompt=example_prompt
    )


def build_request_block() -> ChatPromptTemplate:
    """部件 4:当前制作需求。"""
    return ChatPromptTemplate.from_messages([("human", "{request}")])


def build_forge_prompt(examples: list[dict]) -> ChatPromptTemplate:
    """组装主模板(通用版,变量全开)。"""
    return ChatPromptTemplate.from_messages(
        [
            build_persona_block(),
            build_format_block(),
            build_fewshot_block(examples),
            build_request_block(),
        ]
    )


def make_sect_forge(
    prompt: ChatPromptTemplate, sect: str, format_spec: str
) -> ChatPromptTemplate:
    """预绑定社团与格式,返回该社团专用黑糖资料室模板。

    partial 返回新对象、不改原模板;被绑变量从 input_variables 消失。
    """
    return prompt.partial(sect=sect, format_spec=format_spec)


def render_and_show(prompt: ChatPromptTemplate, variables: dict) -> None:
    """渲染并打印消息(示例块太长,只打首尾以观其形)。"""
    try:
        messages = prompt.invoke(variables).to_messages()
    except KeyError as exc:
        raise KeyError(f"模板渲染失败,缺少变量: {exc.args[0]}") from exc
    # 打印头两条 system 与最后一条 human,中间示例略去
    for msg in messages[:2] + messages[-1:]:
        print(f"  [{msg.type}] {msg.content}")


def main() -> None:
    base = build_forge_prompt(FORGE_EXAMPLES)
    print("预绑定前的变量:", sorted(base.input_variables))

    # 一份主模板,派生两个社团变体——配置在派生时锁定
    xuantie = make_sect_forge(base, "素材组", "《方案名称》类型|尺寸|重量|优化细节|特性")
    baihua = make_sect_forge(base, "视觉设计组", "《方案名称》类型|尺寸|重量|花淬|特性")

    # 调用契约收窄:从 3 个变量缩到 1 个
    print("预绑定后(素材组)的变量:", sorted(xuantie.input_variables))
    print("素材组锁定的配置:", sorted(xuantie.partial_variables))

    print("--- 素材组开始处理 ---")
    render_and_show(xuantie, {"request": "校园活动长篇方案,使用高分辨率图片与品牌色"})

    print("--- 视觉设计组开始处理 ---")
    render_and_show(baihua, {"request": "一份缠枝长图海报,主材精钢"})


if __name__ == "__main__":
    main()
