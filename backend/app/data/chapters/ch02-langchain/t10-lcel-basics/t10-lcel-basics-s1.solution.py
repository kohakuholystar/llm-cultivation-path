"""黑糖资料室 · LCEL 处理管道 · s1：用 LangChain 完成可验证的学习任务。"""
import os
import sys

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_openai import ChatOpenAI

# 配置全部来自环境变量,密钥绝不写死在代码里
MODEL_NAME = os.environ.get("MODEL_NAME", "deepseek-v4-pro")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")


def use_mock() -> bool:
    """MOCK_LLM=1 时进入本地演示模式:用假模型,不联网、不耗 token。"""
    return bool(os.environ.get("MOCK_LLM"))


def check_api_key() -> None:
    """真实模式下必须配置 DeepSeek Key,缺失时优雅退出而不是甩出一屏 traceback。"""
    if use_mock():
        return
    if not os.environ.get("OPENAI_API_KEY"):
        print("请先在右上角 AI 配置填入 DeepSeek API Key")
        sys.exit(0)


def build_llm(temperature: float = 0.7):
    """构建 LLM 组件:两种模式返回同一接口(都有 .invoke),上层代码无感切换。"""
    if use_mock():
        # 假模型按顺序循环吐出预置回答,接口与真模型完全一致
        return FakeListChatModel(responses=[
            "晨光:配色清爽,重点突出,适合作为活动主视觉。",
            "夜蓝:冷色渐变为底,点缀柔和高光,适合夜间活动海报。",
        ])
    # base_url 指向 DeepSeek 的 OpenAI 兼容端点,换供应商不改业务逻辑
    return ChatOpenAI(
        model=MODEL_NAME,
        base_url=BASE_URL,
        temperature=temperature,
        timeout=30,        # 网络异常时 30s 果断超时,不无限挂起
        max_retries=2,     # 偶发抖动自动重试两次
    )


def forge_sword_name(llm, material: str) -> str:
    """调用 LLM,为给定制作素材起方案名并附一句点评。"""
    prompt = f"你是一名内容策划助手。用「{material}」制作一份方案,给出方案名称和一句点评,60 字以内。"
    try:
        resp = llm.invoke(prompt)     # 返回的是 AIMessage 对象
        return resp.content.strip()   # 真正的文本在 .content 属性里
    except Exception as exc:          # 鉴权失败/网络超时统一兜底,不让程序崩
        return f"生成失败:{type(exc).__name__}"


def main() -> None:
    check_api_key()
    llm = build_llm()
    mode = "本地演示(mock)" if use_mock() else "真实 API"
    print(f"处理器号:{MODEL_NAME} @ {BASE_URL} [{mode}]")
    for material in ["活动素材", "校园照片"]:
        print(f"【{material}】{forge_sword_name(llm, material)}")
    print("模型服务已燃,提示词工作台开张。")


if __name__ == "__main__":
    main()
