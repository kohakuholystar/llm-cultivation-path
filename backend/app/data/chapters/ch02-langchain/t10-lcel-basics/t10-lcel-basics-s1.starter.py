"""黑糖资料室 · LCEL 处理管道 · s1：用 LangChain 完成可验证的学习任务。"""

# 学习契约
# - 目标：用 ChatOpenAI 将 DeepSeek 封装成可复用 LLM 组件。
# - 补写：补写 `check_api_key`、`build_llm` 与 `forge_sword_name`。
# - 关键函数/类（入参 → 出参）：`check_api_key() -> None` 校验运行环境；`build_llm(temperature: float)` 返回可调用模型；`forge_sword_name(llm, material: str) -> str` 返回模型文本。
# - 技术栈：LangChain OpenAI、`ChatOpenAI`、FakeListChatModel。
# - 前置条件：真实运行前在右上角 AI 配置填写自己的 DeepSeek API Key；`MOCK_LLM` 可做离线演示。
# - 可观察结果：打印一条由模型生成的素材命名结果。
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
    # TODO: 实现 Key 检查:mock 模式直接放行;真实模式缺 OPENAI_API_KEY 时打印提示并 sys.exit(0)
    # 提示:if use_mock(): 直接 return;Key 用 os.environ.get("OPENAI_API_KEY") 判空,
    #       为空则 print("请先在右上角 AI 配置填入 DeepSeek API Key") 后 sys.exit(0)
    raise NotImplementedError("check_api_key 尚未实现:请按 TODO 提示完成 Key 检查")


def build_llm(temperature: float = 0.7):
    """构建 LLM 组件:两种模式返回同一接口(都有 .invoke),上层代码无感切换。"""
    # TODO: 双分支构造:mock 分支返回 FakeListChatModel,真实分支返回 ChatOpenAI 封装 DeepSeek
    # 提示:if use_mock(): return FakeListChatModel(responses=["回答1", "回答2"]);
    #       真实分支 return ChatOpenAI(model=MODEL_NAME, base_url=BASE_URL,
    #       temperature=temperature, timeout=30, max_retries=2)
    raise NotImplementedError("build_llm 尚未实现:请按 TODO 提示完成双分支构造")


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
