"""渡劫飞升 · s5:配置注入与密钥守卫
部署的灵魂是「配置不进镜像」。本步把所有可变项收进环境变量,
并为密钥上一道守卫:缺 key 时给出引导文案,而不是甩出堆栈 traceback。
"""
import os
import sys
import yaml
from dataclasses import dataclass

MOCK = os.environ.get("MOCK_LLM") == "1"          # 演示模式:无网时走剧本
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("请先在右上角 AI 配置填入 DeepSeek API Key")
    sys.exit(0)

# 编排文件(s3 产物,原样复用;密钥经 environment 注入)
COMPOSE = """# 渡劫飞升 · 编排(由 s3 生成)。
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
ENV_EXAMPLE = """# 渡劫飞升 · 环境配置样例(由 s5 生成)。
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
        return cls(
            host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", "8000")),
            model_name=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
            api_key=os.environ.get("OPENAI_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", ""),
        )


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
