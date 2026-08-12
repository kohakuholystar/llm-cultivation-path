"""运行时观测台 · s2:使用 OpenTelemetry 追踪一次 Agent 回合。"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor


def configure_tracer() -> trace.Tracer:
    """配置本地 Console exporter；生产环境通常换成 OTLP exporter。"""
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    return trace.get_tracer("harness.lesson")


def run_turn(tracer: trace.Tracer, request_id: str) -> None:
    """为入口、模型调用和工具调用创建嵌套 span。"""
    with tracer.start_as_current_span("agent.turn") as turn:
        turn.set_attribute("request.id", request_id)
        turn.set_attribute("llm.model", "deepseek-v4-pro")
        with tracer.start_as_current_span("llm.call") as llm_span:
            llm_span.set_attribute("gen_ai.operation.name", "chat")
        with tracer.start_as_current_span("tool.weather") as tool_span:
            tool_span.set_attribute("tool.name", "weather")
    print("链路追踪就绪：已导出 agent.turn、llm.call、tool.weather")


def main() -> None:
    tracer = configure_tracer()
    run_turn(tracer, "demo-1")


if __name__ == "__main__":
    main()
