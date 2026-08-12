"""运行时观测台 · s2:使用 OpenTelemetry 追踪一次 Agent 回合。"""


# === 学习契约（面向学生）===
# 本节目标：链路追踪:使用 OpenTelemetry 创建真实 Span。完成后能把本节概念放入可运行的工程链路。
# 需要补写：SimpleSpanProcessor、start_as_current_span、run_turn；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `configure_tracer() -> trace.Tracer`：输入为签名中的参数；输出为 `trace.Tracer`。用途：配置本地 Console exporter；生产环境通常换成 OTLP exporter。
#   - `run_turn(tracer: trace.Tracer, request_id: str) -> None`：输入为签名中的参数；输出为 `None`。用途：为入口、模型调用和工具调用创建嵌套 span。
#   - `main() -> None`：输入为签名中的参数；输出为 `None`。用途：按本节调用链完成对应处理
# 所属技术栈/模块：Python 运行时工程：Harness、状态机、上下文、韧性、日志与插件。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor


def configure_tracer() -> trace.Tracer:
    """配置本地 Console exporter；生产环境通常换成 OTLP exporter。"""
    # TODO: 创建 TracerProvider，添加 SimpleSpanProcessor(ConsoleSpanExporter())，并注册。
    # 提示: provider = TracerProvider(); provider.add_span_processor(...);
    #       trace.set_tracer_provider(provider); return trace.get_tracer("harness.lesson")
    raise NotImplementedError("请实现 configure_tracer")


def run_turn(tracer: trace.Tracer, request_id: str) -> None:
    """为入口、模型调用和工具调用创建嵌套 span。"""
    # TODO: 用 tracer.start_as_current_span("agent.turn") 创建根 span。
    # TODO: 根 span 写入 request.id；在内部创建 llm.call 与 tool.weather 子 span。
    # TODO: 不要把 API Key、完整用户提示词或模型输出写进 span 属性。
    raise NotImplementedError("请实现 run_turn")


def main() -> None:
    tracer = configure_tracer()
    # TODO: 调用 run_turn(tracer, "demo-1")，观察 Console exporter 输出的 parent_id 与 name。
    raise NotImplementedError("请完成 main 演示")


if __name__ == "__main__":
    main()
