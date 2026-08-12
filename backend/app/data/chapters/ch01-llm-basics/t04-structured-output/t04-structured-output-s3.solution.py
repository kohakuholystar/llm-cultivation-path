"""星澈助手 · 结构化抽取 v3:解析失败自动重试,把错误反馈给模型"""
import json
import os
import sys

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

MODEL = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
MAX_RETRIES = 2

DEMO_DIALOG = """客服:您好,这里是星澈助手,请问有什么可以帮您?
用户:我昨天充值的会员到现在还没到账,订单号 88231。
客服:非常抱歉,我马上帮您核实订单状态。
用户:麻烦尽快处理,我今晚等着用。"""

# MOCK 剧本:第一次是坏输出(Markdown 包裹 + 订单号非法),第二次才合格
MOCK_SCRIPT = [
    "```json\n{\"issue\": \"会员充值未到账\", \"order_id\": \"abc\", \"emotion\": \"焦急\"}\n```",
    json.dumps({"issue": "会员充值未到账", "order_id": "88231", "emotion": "焦急"},
               ensure_ascii=False),
]
_mock_state = {"n": 0}


class TicketExtract(BaseModel):
    """客服工单的结构化 schema。"""

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
    """发起一次 JSON 模式对话;MOCK 模式按顺序播剧本。"""
    if os.environ.get("MOCK_LLM"):
        idx = min(_mock_state["n"], len(MOCK_SCRIPT) - 1)
        _mock_state["n"] += 1
        return MOCK_SCRIPT[idx]
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    return resp.choices[0].message.content


def parse_ticket(raw: str) -> TicketExtract:
    """json.loads 管语法,model_validate 管语义。"""
    return TicketExtract.model_validate(json.loads(raw))


def extract_with_retry(client: OpenAI, messages: list[dict],
                       max_retries: int = MAX_RETRIES) -> tuple[TicketExtract, int]:
    """抽取并校验;失败时把错误原因追加进对话,让模型带着反馈重来。"""
    history = list(messages)
    for attempt in range(1, max_retries + 1):
        raw = chat_once(client, history)
        try:
            return parse_ticket(raw), attempt
        except (json.JSONDecodeError, ValidationError) as exc:
            brief = str(exc).splitlines()[0]
            print(f"[重试] 第 {attempt} 次输出未过校验: {brief}")
            # 把坏输出和错误原因喂回去,下一轮 prompt 自带"错题本"
            history.append({"role": "assistant", "content": raw})
            history.append({"role": "user", "content": (
                f"你上一次的输出未通过校验:{brief}。"
                "请只输出一个合法 JSON 对象,不要 Markdown 代码块,字段严格符合要求。"
            )})
    raise RuntimeError(f"连续 {max_retries} 次抽取失败,转人工处理")


def main() -> None:
    client = build_client()
    messages = [
        {"role": "system", "content": (
            "你是星澈助手客服质检助手。请从对话中抽取关键信息,"
            "只输出一个 JSON 对象,包含 issue、order_id、emotion 三个字段。"
        )},
        {"role": "user", "content": DEMO_DIALOG},
    ]
    try:
        ticket, attempts = extract_with_retry(client, messages)
    except RuntimeError as exc:
        print(f"[星澈助手] {exc}")
        sys.exit(1)
    print(f"[星澈助手] 第 {attempts} 次尝试后抽取成功:")
    print(ticket.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
