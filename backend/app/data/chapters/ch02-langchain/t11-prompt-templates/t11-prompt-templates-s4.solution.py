"""铸剑台 · 模板工程 第 4 步:partial 预绑定变量。

同一套主模板,不同门派的铸剑台要长期固定 sect 与 format_spec:
那是"配置",不是每次的"输入"。.partial() 预绑定配置、收窄调用契约,
派生出各门派的专用变体——主模板升级,所有变体自动受益。
在第 3 步基础上扩展:部件与组装不变,新增派生层。
"""

from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
)
from langchain_core.messages import BaseMessage

FORGE_EXAMPLES = [
    {"request": "轻巧短剑,适合贴身暗卫",
     "recipe": "《鱼肠》双刃短剑|长一尺二寸|重一斤|淬火:寒潭水|特性:藏锋"},
    {"request": "马上用的长刀,要劈砍有力",
     "recipe": "《破阵》环首长刀|长四尺|重八斤|淬火:桐油|特性:势沉"},
]


def build_persona_block() -> ChatPromptTemplate:
    """部件 1:铸剑师人设。"""
    return ChatPromptTemplate.from_messages(
        [("system", "你是铸剑台的总铸剑师,出身门派「{sect}」,铸剑六十年。")]
    )


def build_format_block() -> ChatPromptTemplate:
    """部件 2:剑谱格式要求。"""
    return ChatPromptTemplate.from_messages(
        [("system", "剑谱必须遵循以下格式:{format_spec}")]
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
    """部件 4:当前铸剑需求。"""
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
    """预绑定门派与格式,返回该门派专用铸剑台模板。

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

    # 一份主模板,派生两个门派变体——配置在派生时锁定
    xuantie = make_sect_forge(base, "玄铁阁", "《剑名》类型|尺寸|重量|淬火|特性")
    baihua = make_sect_forge(base, "百花谷", "《剑名》类型|尺寸|重量|花淬|特性")

    # 调用契约收窄:从 3 个变量缩到 1 个
    print("预绑定后(玄铁阁)的变量:", sorted(xuantie.input_variables))
    print("玄铁阁锁定的配置:", sorted(xuantie.partial_variables))

    print("--- 玄铁阁开炉 ---")
    render_and_show(xuantie, {"request": "镇派重剑,主材玄铁精金"})

    print("--- 百花谷开炉 ---")
    render_and_show(baihua, {"request": "一柄缠枝细剑,主材精钢"})


if __name__ == "__main__":
    main()
