"""校园 AI 社辩论 · s5:完整辩论流水线总装

前四步分别实现了立场、交锋、裁决与共识,本步把它们组装成一条
完整流水线,并用 @dataclass 把整场辩论打包成一份报告。真实 LLM
调用全部包在 try/except 里:任何一步失败都降级为预设结果,保证
演示永不中断——这是多 Agent 系统接入外部模型时的兜底姿势。
"""


# === 学习契约（面向学生）===
# 本节目标：校园 AI 社总装:完整辩论流水线。完成后能把本节概念放入可运行的工程链路。
# 需要补写：本文件中标有 TODO 的函数或类方法；只补全 TODO，不改变既有接口、断言或执行顺序。
# 关键函数/类（输入与输出）：
#   - `mock_transcript() -> list[str]`：输入为签名中的参数；输出为 `list[str]`。用途：剧本模式下的完整辩论记录:两条立论 + 两轮交锋。
#   - `build_llm() -> ChatOpenAI`：输入为签名中的参数；输出为 `ChatOpenAI`。用途：构建 DeepSeek 兼容客户端,低温保证输出稳定。
#   - `mock_verdict_text() -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `mock_final_stance(name: str, stance: str) -> str`：输入为签名中的参数；输出为 `str`。用途：按本节调用链完成对应处理
#   - `run_debate(rounds: int=2) -> DebateReport`：输入为签名中的参数；输出为 `DebateReport`。用途：跑完整场辩论并返回报告;LLM 不可用时自动降级。
#   - `print_report(report: DebateReport) -> None`：输入为签名中的参数；输出为 `None`。用途：把整场辩论的结果打印成易读报告。
#   - `Debater`：承载本节状态/数据；重点方法：见类定义。
#   - `Judge`：承载本节状态/数据；重点方法：verdict。
#   - `Consensus`：承载本节状态/数据；重点方法：ask_final_stance, check_convergence。
#   - `DebateReport`：承载本节状态/数据；重点方法：见类定义。
# 所属技术栈/模块：多 Agent 工程：消息协议、LangGraph StateGraph、条件边、人工复核；CrewAI 仅作对照原型。
# 前置条件：无需联网；按文件中的依赖导入和本地运行环境执行。
# 可观察结果：运行本文件后，应看到任务规定的状态、报告或验证输出；通过测试/断言即表示本节契约成立。
# === 学习契约结束 ===
import os
import sys
from dataclasses import dataclass

from langchain_openai import ChatOpenAI

DEBATE_TOPIC = "校园 AI 社的校园助手服务该由 Agent 全自动上线,还是保留人工复核?"

MOCK = os.environ.get("MOCK_LLM") == "1"
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("未检测到 API Key:请先在右上角 AI 配置填入 DeepSeek API Key。")
    print("(本地离线演示可设 MOCK_LLM=1,全流程使用剧本)")
    sys.exit(0)


class Debater:
    """极简辩论员:只负责携带身份与立场。"""

    def __init__(self, name: str, role: str, stance: str) -> None:
        self.name, self.role, self.stance = name, role, stance


def mock_transcript() -> list[str]:
    """剧本模式下的完整辩论记录:两条立论 + 两轮交锋。"""
    return [
        "正方·产品负责人 立论:校园助手服务流程已全面自动化,Agent 上线又快又稳,人工复核纯属拖后腿。",
        "反方·风险审查员 立论:校园助手服务关系校园 AI 社民生,一旦 Agent 决策失误影响面巨大,必须保留人工复核。",
        "[第1轮] 正方·产品负责人:自动化能把错误率压到接近零,人工复核反而引入主观偏差。",
        "[第1轮] 反方·风险审查员:校园助手一旦误判,影响的是成千上万使用者,快不等于对。",
        "[第2轮] 正方·产品负责人:先全自动上线再灰度观测,比事事等人拍板更快暴露问题。",
        "[第2轮] 反方·风险审查员:人工复核不是拖慢上线,而是给 Agent 的决策兜底。",
    ]


def build_llm() -> ChatOpenAI:
    """构建 DeepSeek 兼容客户端,低温保证输出稳定。"""
    # TODO: 返回 ChatOpenAI 客户端,模型/密钥/地址从环境变量读,温度设 0
    # 提示: return ChatOpenAI(
    #           model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
    #           api_key=os.environ.get("OPENAI_API_KEY"),
    #           base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
    #           temperature=0,
    #       )
    raise NotImplementedError("t52-debate-s5 尚未实现:请按 TODO 提示补齐 build_llm 客户端")


JUDGE_PROMPT_TEMPLATE = (
    "你是校园 AI 社评审员社长,主持这场关于「{topic}」的正式辩论。\n"
    "以下是完整辩论记录:\n{transcript}\n"
    "请只回复三行,不要多余内容:\n胜方:<正方·产品负责人 / 反方·风险审查员>\n"
    "理由:<一句话>\n"
    "置信度:<0 到 1 之间的小数>"
)


def mock_verdict_text() -> str:
    return "胜方:反方·风险审查员\n理由:校园助手服务关系民生,人工复核的兜底价值更高。\n置信度:0.8"


class Judge:
    """中立评审员:读完整场辩论,给出结构化裁决。"""

    def __init__(self) -> None:
        self.llm = None if MOCK else build_llm()

    def verdict(self, transcript: list[str]) -> dict[str, object]:
        # TODO: 拼裁决提示词;MOCK 走剧本,否则调模型;逐行解析三字段返回结构化结果
        # 提示: prompt = JUDGE_PROMPT_TEMPLATE.format(topic=DEBATE_TOPIC, transcript="\n".join(transcript))
        #       if MOCK: raw = mock_verdict_text() else: raw = self.llm.invoke(prompt).content
        #       result = {}; 逐行按 胜方:/理由:/置信度: 前缀解析,置信度 float()
        #       return result
        raise NotImplementedError("t52-debate-s5 尚未实现:请按 TODO 提示补齐 verdict 裁决")


FINAL_STANCE_PROMPT_TEMPLATE = (
    "你是校园 AI 社辩手「{role}·{name}」,立场「{stance}」。听完对方全部发言后,"
    "请只回复一个词给出你的最终立场:支持或反对。\n"
    "完整辩论记录:\n{transcript}"
)


def mock_final_stance(name: str, stance: str) -> str:
    return "反对" if name == "产品负责人" else stance


class Consensus:
    """共识检测器:收集最终立场,判断双方是否收敛。"""

    def __init__(self) -> None:
        self.llm = None if MOCK else build_llm()

    def ask_final_stance(self, debater: Debater, transcript: list[str]) -> str:
        # TODO: MOCK 走剧本,否则拼提示词调模型;把回复归一化成支持/反对
        # 提示: if MOCK: raw = mock_final_stance(debater.name, debater.stance)
        #       else: prompt = FINAL_STANCE_PROMPT_TEMPLATE.format(role=..., name=..., stance=..., transcript="\n".join(transcript))
        #            raw = self.llm.invoke(prompt).content
        #       return "支持" if "支持" in str(raw) else "反对"
        raise NotImplementedError("t52-debate-s5 尚未实现:请按 TODO 提示补齐 ask_final_stance 表态")

    def check_convergence(self, final: dict[str, str]) -> tuple[bool, str]:
        stance = next(iter(final.values()))
        if all(s == stance for s in final.values()):
            return True, f"双方达成共识,均持「{stance}」立场"
        return False, "双方仍各执己见,未收敛"


@dataclass
class DebateReport:
    """整场辩论的最终报告。"""

    topic: str
    debaters: list[Debater]
    transcript: list[str]
    verdict: dict[str, object]
    final_stances: dict[str, str]
    converged: bool
    note: str


def run_debate(rounds: int = 2) -> DebateReport:
    """跑完整场辩论并返回报告;LLM 不可用时自动降级。"""
    debaters = [Debater("产品负责人", "正方", "支持"), Debater("风险审查员", "反方", "反对")]
    transcript = mock_transcript()
    judge = Judge()
    # TODO: 用 try/except 包住裁决调用,异常降级为「校园 AI 社驳回」兜底结果
    # 提示: try:
    #           verdict = judge.verdict(transcript)
    #       except Exception as exc:
    #           verdict = {"winner": "校园 AI 社驳回", "reason": f"裁决服务暂不可用: {exc}", "confidence": 0.0}
    raise NotImplementedError("t52-debate-s5 尚未实现:请按 TODO 提示补齐裁决兜底")
    consensus = Consensus()
    final_stances: dict[str, str] = {}
    for d in debaters:
        final_stances[d.name] = consensus.ask_final_stance(d, transcript)
    converged, note = consensus.check_convergence(final_stances)
    return DebateReport(DEBATE_TOPIC, debaters, transcript, verdict, final_stances, converged, note)


def print_report(report: DebateReport) -> None:
    """把整场辩论的结果打印成易读报告。"""
    print(f"[辩题] {report.topic}")
    print(f"[对阵] " + " vs ".join(f"{d.role}·{d.name}({d.stance})" for d in report.debaters))
    print(f"[交锋] 共 {len(report.transcript)} 条发言")
    print(f"[社长裁决] {report.verdict}")
    print(f"[最终立场] {report.final_stances}")
    print(f"[收敛判定] {'已收敛' if report.converged else '未收敛'} —— {report.note}")


if __name__ == "__main__":
    print_report(run_debate())
