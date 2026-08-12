"""星澈助手 · 结构化抽取 v2:用 Pydantic schema 给抽取结果上“类型保险”"""
import json
import os
import sys

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

MODEL = os.environ.get("MODEL_NAME", "deepseek-v4-pro")

DEMO_DIALOG = """客服:您好,这里是星澈助手,请问有什么可以帮您?
用户:我昨天充值的会员到现在还没到账,订单号 88231。
客服:非常抱歉,我马上帮您核实订单状态。
用户:麻烦尽快处理,我今晚等着用。"""


class TicketExtract(BaseModel):
    """客服工单的结构化 schema:字段名、类型、约束一次声明。"""

    issue: str = Field(description="用户反馈的问题,一句话概括")
    order_id: str = Field(pattern=r"^\d{5}$", description="5 位数字订单号")
    emotion: str = Field(description="用户情绪,如:平静、焦急、愤怒")


def build_client() -> OpenAI:
    """构建 DeepSeek 客户端;MOCK_LLM 模式下用假 Key,便于离线演示。"""
    if os.environ.get("MOCK_LLM"):
        return OpenAI(api_key="mock-offline", base_url="https://api.deepseek.com")
    if not os.environ.get("OPENAI_API_KEY"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                  base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"))


def chat_once(client: OpenAI, messages: list[dict]) -> str:
    """发起一次 JSON 模式对话,返回模型文本。"""
    if os.environ.get("MOCK_LLM"):
        return json.dumps(
            {"issue": "会员充值未到账", "order_id": "88231", "emotion": "焦急"},
            ensure_ascii=False,
        )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_object"},  # 强制输出合法 JSON
        temperature=0.0,  # 抽取任务不要随机性
    )
    return resp.choices[0].message.content


def parse_ticket(raw: str) -> TicketExtract:
    """两道关卡:json.loads 保证语法合法,model_validate 保证字段合规。"""
    data = json.loads(raw)
    return TicketExtract.model_validate(data)  # 语义校验:类型 + 正则约束


def main() -> None:
    client = build_client()
    messages = [
        {"role": "system", "content": (
            "你是星澈助手客服质检助手。请从对话中抽取关键信息,"
            "只输出一个 JSON 对象,包含 issue、order_id、emotion 三个字段。"
        )},
        {"role": "user", "content": DEMO_DIALOG},
    ]
    raw = chat_once(client, messages)
    try:
        ticket = parse_ticket(raw)
    except json.JSONDecodeError:
        print("[星澈助手] 输出不是合法 JSON,原文如下:")
        print(raw)
        sys.exit(1)
    except ValidationError as exc:
        # Pydantic 会给出精确到字段的错误报告
        print("[星澈助手] 字段校验未通过:")
        print(exc)
        sys.exit(1)
    print("[星澈助手] 校验通过的工单:")
    print(ticket.model_dump_json(indent=2))
    print(f"摘要: 订单 {ticket.order_id} | 情绪 {ticket.emotion} | {ticket.issue}")


if __name__ == "__main__":
    main()
