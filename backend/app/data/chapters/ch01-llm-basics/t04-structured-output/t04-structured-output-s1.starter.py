"""星澈助手 · 结构化抽取 v1:用 response_format 强制模型输出 JSON"""
# 学习契约
# 目标：完成 t04-structured-output-s1 的可验证实现，并理解它在本章工作流中的职责。
# 补写内容：根据 TODO 完成缺失逻辑（当前包含 2 处待完成提示），不改变既有接口。
# 关键函数/类与入出参：build_client() -> OpenAI; chat_once(client, messages) -> str; main() -> None。
# 技术栈：json, os, sys, openai；前置条件：在右上角 AI 配置填入自己的 DeepSeek API Key。
# 可观察结果：运行 main() 后应输出本步骤的演示结果；通过测试即表示输入、输出与边界条件符合要求。
import json
import os
import sys

from openai import OpenAI

MODEL = os.environ.get("MODEL_NAME", "deepseek-v4-pro")

# 一段客服对话记录,作为抽取对象
DEMO_DIALOG = """客服:您好,这里是星澈助手,请问有什么可以帮您?
用户:我昨天充值的会员到现在还没到账,订单号 88231。
客服:非常抱歉,我马上帮您核实订单状态。
用户:麻烦尽快处理,我今晚等着用。"""


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
    """发起一次对话请求,返回模型的文本内容。"""
    if os.environ.get("MOCK_LLM"):
        # 离线演示:返回一段固定的合法 JSON
        return json.dumps(
            {"issue": "会员充值未到账", "order_id": "88231", "emotion": "焦急"},
            ensure_ascii=False,
        )
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        # TODO: 补两个参数——response_format={"type": "json_object"} 强制输出 JSON;
        #       temperature=0.0 消除抽取的随机性
    )
    return resp.choices[0].message.content


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
    # TODO: 用 json.loads(raw) 把模型输出解析为 dict,存入变量 data
    print("[星澈助手] 抽取结果:")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
