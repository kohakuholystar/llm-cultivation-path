"""星澈助手 · 结构化抽取 v4:few-shot 示例锁定格式与标签空间"""
# 学习契约
# 目标：完成 t04-structured-output-s4 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 2 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：build_client() -> OpenAI; build_messages(dialog) -> list[dict]; chat_once(client, messages) -> str; parse_ticket(raw) -> TicketExtract。
# 技术栈：json, os, sys, typing, openai；前置条件：在右上角 AI 配置填入自己的 DeepSeek API Key。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
import json
import os
import sys
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

MODEL = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
MAX_RETRIES = 2

DEMO_DIALOG = """客服:您好,这里是星澈助手,请问有什么可以帮您?
用户:我昨天充值的会员到现在还没到账,订单号 88231。
客服:非常抱歉,我马上帮您核实订单状态。
用户:麻烦尽快处理,我今晚等着用。"""

# 两组示例覆盖不同的情绪与优先级,给模型一个可模仿的"标准答案"
FEW_SHOT_EXAMPLES = [
    {"dialog": "用户:你好,订单 10567 的物流三天没更新了,帮忙看下?",
     "answer": {"issue": "物流信息未更新", "order_id": "10567",
                "emotion": "平静", "priority": "中"}},
    {"dialog": "用户:你们扣了我两次钱!订单 20988,今天必须退!",
     "answer": {"issue": "重复扣费", "order_id": "20988",
                "emotion": "愤怒", "priority": "高"}},
]


class TicketExtract(BaseModel):
    """schema 升级:情绪与优先级用 Literal 锁死取值空间。"""

    issue: str = Field(description="用户反馈的问题,一句话概括")
    order_id: str = Field(pattern=r"^\d{5}$", description="5 位数字订单号")
    # TODO: emotion 改为 Literal["平静", "焦急", "愤怒"],priority 改为
    #       Literal["低", "中", "高"],各自保留 Field(description=...)


def build_client() -> OpenAI:
    """构建 DeepSeek 客户端;MOCK_LLM 模式下用假 Key,便于离线演示。"""
    if os.environ.get("MOCK_LLM"):
        return OpenAI(api_key="mock-offline", base_url="https://api.deepseek.com")
    if not os.environ.get("OPENAI_API_KEY"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                  base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"))


def build_messages(dialog: str) -> list[dict]:
    """组装带 few-shot 示例的消息列表。"""
    lines = [
        "你是星澈助手客服质检助手。请从对话中抽取关键信息,",
        "只输出一个 JSON 对象,字段为 issue、order_id、emotion、priority。",
        "emotion 只能是 平静/焦急/愤怒,priority 只能是 低/中/高。",
        "参考示例:",
    ]
    # TODO: 遍历 FEW_SHOT_EXAMPLES,向 lines 追加
    #       f"对话:{ex['dialog']}" 与 f"输出:{json.dumps(ex['answer'], ensure_ascii=False)}"
    return [
        {"role": "system", "content": "\n".join(lines)},
        {"role": "user", "content": dialog},
    ]


def chat_once(client: OpenAI, messages: list[dict]) -> str:
    if os.environ.get("MOCK_LLM"):
        return json.dumps({"issue": "会员充值未到账", "order_id": "88231",
                           "emotion": "焦急", "priority": "高"}, ensure_ascii=False)
    resp = client.chat.completions.create(
        model=MODEL, messages=messages,
        response_format={"type": "json_object"}, temperature=0.0,
    )
    return resp.choices[0].message.content


def parse_ticket(raw: str) -> TicketExtract:
    """json.loads 管语法,model_validate 管语义。"""
    return TicketExtract.model_validate(json.loads(raw))


def extract_with_retry(client: OpenAI, messages: list[dict],
                       max_retries: int = MAX_RETRIES) -> tuple[TicketExtract, int]:
    """抽取并校验;失败时把错误原因追加进对话重试。"""
    history = list(messages)
    for attempt in range(1, max_retries + 1):
        raw = chat_once(client, history)
        try:
            return parse_ticket(raw), attempt
        except (json.JSONDecodeError, ValidationError) as exc:
            brief = str(exc).splitlines()[0]
            print(f"[重试] 第 {attempt} 次输出未过校验: {brief}")
            history.append({"role": "assistant", "content": raw})
            history.append({"role": "user", "content": (
                f"你上一次的输出未通过校验:{brief}。"
                "请只输出一个合法 JSON 对象,字段严格符合要求。"
            )})
    raise RuntimeError(f"连续 {max_retries} 次抽取失败,转人工处理")


def main() -> None:
    client = build_client()
    messages = build_messages(DEMO_DIALOG)
    print("[星澈助手] system prompt 预览(含 few-shot 示例):")
    print(messages[0]["content"])
    print("-" * 40)
    try:
        ticket, attempts = extract_with_retry(client, messages)
    except RuntimeError as exc:
        print(f"[星澈助手] {exc}")
        sys.exit(1)
    print(f"[星澈助手] 第 {attempts} 次尝试后抽取成功:")
    print(ticket.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
