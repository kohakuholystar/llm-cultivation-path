"""灵讯通 · 结构化抽取 v5:封装成可复用的 TicketExtractor 工具类"""
import json, os, sys
from dataclasses import dataclass
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

MODEL = os.environ.get("MODEL_NAME", "deepseek-v4-pro")

DIALOGS = ["用户:我昨天充值的会员到现在还没到账,订单号 88231。麻烦尽快处理!", "用户:订单 10567 的物流三天没更新了,帮忙看下?", "用户:你们扣了我两次钱!订单 20988,今天必须退!"]
FEW_SHOT = [("用户:你好,订单 10567 的物流三天没更新了,帮忙看下?", {"issue": "物流信息未更新", "order_id": "10567", "emotion": "平静", "priority": "中"}),
            ("用户:你们扣了我两次钱!订单 20988,今天必须退!", {"issue": "重复扣费", "order_id": "20988", "emotion": "愤怒", "priority": "高"})]
# MOCK 剧本按 _chat 调用顺序消费:第二条对话连给两次坏输出,演示重试耗尽转人工
MOCK_TABLE = [{"issue": "会员充值未到账", "order_id": "88231", "emotion": "焦急", "priority": "高"},
              "```json\n{\"issue\": \"物流未更新\", \"order_id\": \"abc\"}\n```",
              "{\"issue\": \"物流未更新\", \"order_id\": \"abc\", \"emotion\": \"无语\", \"priority\": \"中\"}",
              {"issue": "重复扣费", "order_id": "20988", "emotion": "愤怒", "priority": "高"}]


class TicketExtract(BaseModel):
    """工单 schema:Literal 锁死枚举取值。"""
    issue: str = Field(description="用户反馈的问题,一句话概括")
    order_id: str = Field(pattern=r"^\d{5}$", description="5 位数字订单号")
    emotion: Literal["平静", "焦急", "愤怒"] = Field(description="用户情绪,三选一")
    priority: Literal["低", "中", "高"] = Field(description="处理优先级,三选一")


@dataclass
class ExtractResult:
    """单条结果:成功带工单,失败带错误原因。"""
    dialog: str
    ticket: TicketExtract | None = None
    error: str | None = None
    attempts: int = 0

    @property
    def ok(self) -> bool:
        return self.ticket is not None


def build_client() -> OpenAI:
    """构建 DeepSeek 客户端;MOCK_LLM 模式下离线演示。"""
    if os.environ.get("MOCK_LLM"):
        return OpenAI(api_key="mock-offline", base_url="https://api.deepseek.com")
    if not os.environ.get("OPENAI_API_KEY"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"))


class TicketExtractor:
    """对话 → 结构化工单:few-shot + JSON 模式 + 自动重试 + 失败隔离。"""

    def __init__(self, client: OpenAI, max_retries: int = 2):
        self.client = client
        self.max_retries = max_retries
        self._mock_n = 0  # MOCK 模式下按序取剧本

    def _chat(self, messages: list[dict]) -> str:
        if os.environ.get("MOCK_LLM"):
            item = MOCK_TABLE[min(self._mock_n, len(MOCK_TABLE) - 1)]
            self._mock_n += 1
            return item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
        resp = self.client.chat.completions.create(
            model=MODEL, messages=messages,
            response_format={"type": "json_object"}, temperature=0.0)
        return resp.choices[0].message.content

    def _messages(self, dialog: str) -> list[dict]:
        head = "你是灵讯通客服质检助手。只输出一个 JSON 对象,字段为 issue、order_id、emotion、priority。"
        shots = [f"对话:{d} 输出:{json.dumps(a, ensure_ascii=False)}" for d, a in FEW_SHOT]
        return [{"role": "system", "content": "\n".join([head, "参考示例:"] + shots)}, {"role": "user", "content": dialog}]

    def extract(self, dialog: str) -> ExtractResult:
        """单条抽取:失败重试,耗尽后记错误而非抛异常。"""
        history = self._messages(dialog)
        for attempt in range(1, self.max_retries + 1):
            raw = self._chat(history)
            try:
                ticket = TicketExtract.model_validate(json.loads(raw))
                return ExtractResult(dialog=dialog, ticket=ticket, attempts=attempt)
            except (json.JSONDecodeError, ValidationError) as exc:
                brief = str(exc).splitlines()[0]
                print(f"[重试] 第 {attempt} 次未过校验: {brief}")
                history.append({"role": "assistant", "content": raw})
                history.append({"role": "user", "content": f"上次输出未过校验:{brief},请只输出合法 JSON。"})
        return ExtractResult(dialog=dialog, error=brief, attempts=self.max_retries)

    def batch_extract(self, dialogs: list[str]) -> list[ExtractResult]:
        """批量抽取:逐条隔离,单条失败不拖垮整批。"""
        return [self.extract(d) for d in dialogs]


def main() -> None:
    results = TicketExtractor(build_client()).batch_extract(DIALOGS)
    for i, r in enumerate(results, 1):
        if r.ok:
            print(f"[{i}] 成功(第 {r.attempts} 次): 订单 {r.ticket.order_id} | {r.ticket.priority} | {r.ticket.emotion} | {r.ticket.issue}")
        else:
            print(f"[{i}] 失败(已转人工): {r.error}")
    print(f"批量完成: {sum(1 for r in results if r.ok)}/{len(results)} 条成功")


if __name__ == "__main__":
    main()
