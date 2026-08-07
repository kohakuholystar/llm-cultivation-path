"""铸剑台 · 模板工程 第 5 步:变量校验与健壮渲染(收官版)。

铸剑台要交给师门用:有人漏传参数,有人夹带私货。模板自带的 KeyError 只管
"缺"不管"多",本步加安全渲染层:校验前移、错误中文化、失败短路。
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
    """组装通用主模板。"""
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
    """partial 预绑定门派配置,派生专用变体。"""
    return prompt.partial(sect=sect, format_spec=format_spec)


def validate_variables(prompt: ChatPromptTemplate, data: dict) -> list[str]:
    """对比模板签名与实际传参,返回问题清单(空列表 = 校验通过)。
    模板全部变量 = input_variables + partial_variables,两者都要算进校验。"""
    # TODO: 对比模板签名与实际传参,缺参、多传各归类为中文问题,返回清单
    # 提示: required = set(prompt.input_variables); provided = set(data);
    #       sorted(required - provided) → "缺少必需变量: {name}";
    #       sorted(provided - required) → 已被 partial 绑定则提示无需再传,
    #       否则提示多传了无用变量
    raise NotImplementedError("validate_variables 尚未实现:请按 TODO 提示实现变量校验")


def render_prompt(prompt: ChatPromptTemplate, data: dict) -> str | None:
    """安全渲染:校验通过才开炉;失败打印清单并短路返回 None。"""
    # TODO: 先校验再渲染:有问题逐条打印并短路返回 None,通过才 invoke
    # 提示: problems = validate_variables(prompt, data);
    #       若有问题逐条 print("[校验失败]", p) 后 return None;
    #       否则 try: return prompt.invoke(data).to_string(),
    #       except KeyError 时打印 "[渲染失败] 缺少变量:" 并 return None
    raise NotImplementedError("render_prompt 尚未实现:请按 TODO 提示实现安全渲染")


def main() -> None:
    forge = make_sect_forge(
        build_forge_prompt(FORGE_EXAMPLES),
        "玄铁阁",
        "《剑名》类型|尺寸|重量|淬火|特性",
    )

    # 自检:把模板的调用契约亮出来
    print("=== 铸剑台模板自检 ===")
    print("必需变量:", sorted(forge.input_variables))
    print("已绑变量:", sorted(forge.partial_variables))

    print("=== 正常开炉 ===")  # 场景 1:传参规范
    text = render_prompt(forge, {"request": "镇派宝剑,主材玄铁精金"})
    if text:
        print(text[:120], "...")

    print("=== 缺参演练 ===")  # 场景 2:漏传 request,被拦下
    render_prompt(forge, {})

    print("=== 多参演练 ===")  # 场景 3:夹带已绑定的 sect,被点名
    render_prompt(forge, {"request": "匕首", "sect": "不该传的"})


if __name__ == "__main__":
    main()
