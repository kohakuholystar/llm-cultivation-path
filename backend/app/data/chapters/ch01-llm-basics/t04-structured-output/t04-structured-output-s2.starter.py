"""星澈助手 · 结构化抽取 v2:用 Pydantic schema 给抽取结果上“类型保险”"""
# 学习契约
# 目标：完成 t04-structured-output-s2 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 2 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：build_client() -> OpenAI; chat_once(client, messages) -> str; parse_ticket(raw) -> 'TicketExtract'; main() -> None。
# 技术栈：json, os, sys, openai, pydantic；前置条件：在右上角 AI 配置填入自己的 DeepSeek API Key。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
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


# TODO: 定义 class TicketExtract(BaseModel),声明三个字段:
#   issue: str = Field(description="用户反馈的问题,一句话概括")
#   order_id: str = Field(pattern=r"^\d{5}$", description="5 位数字订单号")
#   emotion: str = Field(description="用户情绪,如:平静、焦急、愤怒")


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
        model=MODEL, messages=messages,
        response_format={"type": "json_object"}, temperature=0.0,
    )
    return resp.choices[0].message.content


def parse_ticket(raw: str) -> "TicketExtract":
    """两道关卡:json.loads 管语法,model_validate 管语义。"""
    data = json.loads(raw)
    # TODO: 用 TicketExtract.model_validate(data) 校验并返回工单对象


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
    ticket = parse_ticket(raw)
    print("[星澈助手] 校验通过的工单:")
    print(ticket.model_dump_json(indent=2))
    print(f"摘要: 订单 {ticket.order_id} | 情绪 {ticket.emotion} | {ticket.issue}")


if __name__ == "__main__":
    main()
