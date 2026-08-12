"""终期交付 · s5:配置注入与密钥守卫
部署的灵魂是「配置不进镜像」。本步把所有可变项收进环境变量,
并为密钥上一道守卫:缺 key 时给出引导文案,而不是甩出堆栈 traceback。
"""


# === 学习契约（面向学生）===
# 本节目标：配置注入与密钥守卫。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `audit_compose(text: str) -> list[str]`：输入为签名中的参数；输出为 `list[str]`。用途：解析 compose 文本,校验服务、端口、环境与健康检查,返回问题清单。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
#   - `Config`：承载本节状态/数据；重点方法：from_env。
# 所属技术栈/模块：应用交付：RAG、Agent、FastAPI、Docker、pytest、性能与上线验收。
# 前置条件：需要在右上角 AI 配置填写自己的 DeepSeek API Key，并允许本节联网运行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import os
import sys
import yaml
from dataclasses import dataclass

MOCK = os.environ.get("MOCK_LLM") == "1"          # 演示模式:无网时走剧本
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("请先在右上角 AI 配置填入 DeepSeek API Key")
    sys.exit(0)

# 编排文件(s3 产物,原样复用;密钥经 environment 注入)
COMPOSE = """# 黑糖资料室 · 编排(由 s3 生成)。
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DEEPSEEK_API_KEY: "${DEEPSEEK_API_KEY:?请在 .env 中配置}"
      MODEL_NAME: deepseek-v4-pro
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
"""


def audit_compose(text: str) -> list[str]:
    """解析 compose 文本,校验服务、端口、环境与健康检查,返回问题清单。"""
    problems = []
    try:
        data = yaml.safe_load(text) or {}
    except Exception as exc:
        return [f"compose 无法解析: {exc}"]
    services = data.get("services") or {}
    if not services:
        problems.append("services 为空,至少要有 app 服务")
    app = services.get("app") or {}
    if "build" not in app:
        problems.append("app 缺少 build 指令,镜像从哪来?")
    if app.get("ports") != ["8000:8000"]:
        problems.append("端口映射应为 8000:8000")
    env = app.get("environment") or {}
    if "DEEPSEEK_API_KEY" not in env:
        problems.append("environment 缺少 DEEPSEEK_API_KEY 注入")
    if "healthcheck" not in app:
        problems.append("app 缺少 healthcheck,容器挂了自己都不知道")
    return problems


# 环境配置样例:复制为 .env 后按需修改,密钥本体绝不允许进仓库
ENV_EXAMPLE = """# 黑糖资料室 · 环境配置样例(由 s5 生成)。
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
MODEL_NAME=deepseek-v4-pro
PORT=8000
"""


@dataclass
class Config:
    """部署配置:全部来自环境变量,带默认值与校验。"""

    host: str = "0.0.0.0"
    port: int = 8000
    model_name: str = "deepseek-v4-pro"
    api_key: str = ""

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量构造配置,拿不到就用默认值。"""
        # TODO: 用 os.environ.get 读取四个环境变量并返回 Config,全部带默认值
        # 提示: host 取 "HOST"(默认 "0.0.0.0");port 取 int(os.environ.get("PORT", "8000"));
        #       model_name 取 "MODEL_NAME"(默认 "deepseek-v4-pro");
        #       api_key 先读 "OPENAI_API_KEY" 再回退 "DEEPSEEK_API_KEY";
        #       return cls(host=..., port=..., model_name=..., api_key=...)
        raise NotImplementedError("t73-docker-deploy-s5 尚未实现:请按 TODO 提示从环境变量构造 Config")


def main() -> None:
    cfg = Config.from_env()
    with open(".env.example", "w", encoding="utf-8") as f:
        f.write(ENV_EXAMPLE)
    print("== 配置注入检查 ==")
    print(f"  服务监听  {cfg.host}:{cfg.port}")
    print(f"  模型      {cfg.model_name}")
    masked = cfg.api_key[:4] + "****" if cfg.api_key else "(未配置)"
    print(f"  密钥      {masked}")
    if not cfg.api_key and MOCK:
        print("  [演示] 演示模式不强制密钥,继续输出部署检查。")
    print("== compose 环境注入 ==")
    problems = audit_compose(COMPOSE)
    print("  全部合格" if not problems else "  " + " ".join(problems))
    print("  铁律:密钥只走环境变量/Secret,绝不写进镜像与代码仓库。")


if __name__ == "__main__":
    main()
