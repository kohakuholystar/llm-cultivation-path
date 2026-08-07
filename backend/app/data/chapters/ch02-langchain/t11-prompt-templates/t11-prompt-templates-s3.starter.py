"""铸剑台 · 模板工程 第 3 步:模板组合与复用。

模板像乐高:人设块、格式块、示例块、需求块各自独立定义、独立测试,
再用 from_messages 一次拼成主模板。from_messages 的列表元素可以直接
放子模板对象,组装时按声明顺序展开,变量自动求并集。
在第 2 步基础上重构:内容不变,结构组件化。
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
    """可复用部件 1:铸剑师人设(只需 sect 变量)。"""
    return ChatPromptTemplate.from_messages(
        [("system", "你是铸剑台的总铸剑师,出身门派「{sect}」,铸剑六十年。")]
    )


def build_format_block() -> ChatPromptTemplate:
    """可复用部件 2:输出格式要求(只需 format_spec 变量)。

    独立成块后,这套格式要求可以原样插进鉴剑台、淬火炉等其他模板。
    """
    # TODO: 返回格式要求部件:一条 system 消息,要求剑谱遵循 {format_spec}
    # 提示: ChatPromptTemplate.from_messages(
    #       [("system", "剑谱必须遵循以下格式:{format_spec}")])
    raise NotImplementedError("build_format_block 尚未实现:请按 TODO 提示构建格式部件")


def build_fewshot_block(examples: list[dict]) -> FewShotChatMessagePromptTemplate:
    """可复用部件 3:示例库消息块(沿用第 2 步写法)。"""
    if not examples:
        raise ValueError("few-shot 示例库不能为空")
    example_prompt = ChatPromptTemplate.from_messages(
        [("human", "{request}"), ("ai", "{recipe}")]
    )
    return FewShotChatMessagePromptTemplate(
        examples=examples, example_prompt=example_prompt
    )


def build_request_block() -> ChatPromptTemplate:
    """可复用部件 4:当前铸剑需求。"""
    return ChatPromptTemplate.from_messages([("human", "{request}")])


def build_forge_prompt(examples: list[dict]) -> ChatPromptTemplate:
    """组装主模板:子模板按声明顺序就地展开成完整消息序列。"""
    # TODO: 用 from_messages 一次拼装四个部件工厂的返回值
    # 提示: 列表元素依次为 build_persona_block()、build_format_block()、
    #       build_fewshot_block(examples)、build_request_block()
    raise NotImplementedError("build_forge_prompt 尚未实现:请按 TODO 提示组装主模板")


def render_and_show(prompt: ChatPromptTemplate, variables: dict) -> None:
    """渲染并逐条打印;缺参时给出中文提示。"""
    try:
        messages = prompt.invoke(variables).to_messages()
    except KeyError as exc:
        raise KeyError(f"模板渲染失败,缺少变量: {exc.args[0]}") from exc
    for i, msg in enumerate(messages, 1):
        print(f"{i}. [{msg.type}] {msg.content}")


def main() -> None:
    prompt = build_forge_prompt(FORGE_EXAMPLES)

    # 主模板的变量签名 = 各部件变量的并集,自动汇总无需手工登记
    print("组装后的变量全集:", sorted(prompt.input_variables))

    render_and_show(
        prompt,
        {
            "sect": "玄铁阁",
            "format_spec": "《剑名》类型|尺寸|重量|淬火|特性",
            "request": "一柄走江湖的佩剑,主材百炼钢",
        },
    )


if __name__ == "__main__":
    main()
