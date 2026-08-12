"""黑糖资料室 · 提示词模板工程 · s5：用 LangChain 完成可验证的学习任务。"""

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
    """partial 预绑定社团配置,派生专用变体。"""
    return prompt.partial(sect=sect, format_spec=format_spec)


def validate_variables(prompt: ChatPromptTemplate, data: dict) -> list[str]:
    """对比模板签名与实际传参,返回问题清单(空列表 = 校验通过)。
    模板全部变量 = input_variables + partial_variables,两者都要算进校验。"""
    required = set(prompt.input_variables)
    bound = set(prompt.partial_variables)
    provided = set(data)

    problems: list[str] = []
    for name in sorted(required - provided):
        problems.append(f"缺少必需变量: {name}")
    for name in sorted(provided - required):
        if name in bound:
            problems.append(f"变量 {name} 已被 partial 绑定,无需再传")
        else:
            problems.append(f"多传了无用变量: {name}(模板不认)")
    return problems


def render_prompt(prompt: ChatPromptTemplate, data: dict) -> str | None:
    """安全渲染:校验通过才启动;失败打印清单并短路返回 None。"""
    problems = validate_variables(prompt, data)
    if problems:
        for p in problems:
            print("[校验失败]", p)
        return None  # fail fast:残缺提示词绝不发给模型
    try:
        return prompt.invoke(data).to_string()
    except KeyError as exc:  # 兜底:动态变量等边角情况仍可能漏网
        print("[渲染失败] 缺少变量:", exc.args[0])
        return None


def main() -> None:
    forge = make_sect_forge(
        build_forge_prompt(FORGE_EXAMPLES),
        "素材组",
        "《方案名称》类型|尺寸|重量|优化细节|特性",
    )

    # 自检:把模板的调用契约亮出来
    print("=== 提示词工作台模板自检 ===")
    print("必需变量:", sorted(forge.input_variables))
    print("已绑变量:", sorted(forge.partial_variables))

    print("=== 正常开始处理 ===")  # 场景 1:传参规范
    text = render_prompt(forge, {"request": "校园活动内容方案,使用高分辨率图片与品牌色"})
    if text:
        print(text[:120], "...")

    print("=== 缺参演练 ===")  # 场景 2:漏传 request,被拦下
    render_prompt(forge, {})

    print("=== 多参演练 ===")  # 场景 3:夹带已绑定的 sect,被点名
    render_prompt(forge, {"request": "匕首", "sect": "不该传的"})


if __name__ == "__main__":
    main()
