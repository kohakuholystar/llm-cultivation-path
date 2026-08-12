"""黑糖资料室 · 提示词模板工程 · s3：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：将人设、格式、示例和请求拆成可组合的提示词部件。
# - 补写：补写四个提示词部件与组合模板。
# - 关键函数/类（入参 → 出参）：各 `build_*_block()` 返回一个消息部件；`build_forge_prompt(examples)` 组合完整模板；`render_and_show(prompt, variables) -> None` 展示结果。
# - 技术栈：LangChain Core、消息模板组合。
# - 前置条件：本步不联网；变量名必须在所有部件之间保持一致。
# - 可观察结果：看到模块化提示词拼接后的完整消息。

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
    """可复用部件 1:内容设计师人设(只需 sect 变量)。"""
    return ChatPromptTemplate.from_messages(
        [("system", "你是提示词工作台的提示词负责人,出身团队「{sect}」,内容制作六十年。")]
    )


def build_format_block() -> ChatPromptTemplate:
    """可复用部件 2:输出格式要求(只需 format_spec 变量)。

    独立成块后,这套格式要求可以原样插进质量评审台、优化细节流程等其他模板。
    """
    # TODO: 返回格式要求部件:一条 system 消息,要求交付卡遵循 {format_spec}
    # 提示: ChatPromptTemplate.from_messages(
    #       [("system", "交付卡必须遵循以下格式:{format_spec}")])
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
    """可复用部件 4:当前制作需求。"""
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
            "sect": "素材组",
            "format_spec": "《方案名称》类型|尺寸|重量|优化细节|特性",
            "request": "一份走技术社区的活动主视觉,主材百炼钢",
        },
    )


if __name__ == "__main__":
    main()
