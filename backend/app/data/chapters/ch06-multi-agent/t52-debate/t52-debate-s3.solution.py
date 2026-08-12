"""校园 AI 社辩论 · s3:中立评审员读全程

交锋记录已就绪,本步请评审员登场:把完整 transcript 交给大模型,
要求它按「胜方 / 理由 / 置信度」三行固定格式裁决,再用解析器把
回复拆回结构化字典。模型说话不可控,「约束 + 解析」是标配。
"""
import os
import sys

from langchain_openai import ChatOpenAI

DEBATE_TOPIC = "校园 AI 社的校园助手服务该由 Agent 全自动上线,还是保留人工复核?"

MOCK = os.environ.get("MOCK_LLM") == "1"
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("未检测到 API Key:请先在右上角 AI 配置填入 DeepSeek API Key。")
    print("(本地离线演示可设 MOCK_LLM=1,用剧本模拟评审员裁决)")
    sys.exit(0)

# 每个立场对应一句开篇立论
OPENING_SCRIPT = {
    "支持": "校园助手服务流程已全面自动化,Agent 上线又快又稳,人工复核纯属拖后腿。",
    "反对": "校园助手服务关系校园 AI 社民生,一旦 Agent 决策失误影响面巨大,必须保留人工复核。",
}

# 反驳词库:每个立场两句,按轮次循环取用
REBUTTAL_SCRIPT = {
    "支持": ["自动化能把错误率压到接近零,人工复核反而引入主观偏差。",
             "先全自动上线再灰度观测,比事事等人拍板更快暴露问题。"],
    "反对": ["校园助手一旦误判,影响的是成千上万使用者,快不等于对。",
             "人工复核不是拖慢上线,而是给 Agent 的决策兜底。"],
}


class Debater:
    """一名立场固定的辩论员。"""

    def __init__(self, name: str, role: str, stance: str) -> None:
        self.name = name
        self.role = role
        self.stance = stance

    def opening_statement(self) -> str:
        return f"{self.role}·{self.name} 立论:{OPENING_SCRIPT[self.stance]}"


class Debate:
    """回合制辩论编排器:记录发言并按轮次轮换取句。"""

    def __init__(self, debaters: list[Debater]) -> None:
        self.debaters = debaters
        self.transcript: list[str] = []
        self._used: dict[str, int] = {}

    def run(self, rounds: int = 2) -> list[str]:
        for d in self.debaters:
            line = d.opening_statement()
            self.transcript.append(line)
            print(line)
        for r in range(1, rounds + 1):
            for d in self.debaters:
                line = f"[第{r}轮] {d.role}·{d.name}:{self.rebut(d)}"
                self.transcript.append(line)
                print(line)
        return self.transcript

    def rebut(self, debater: Debater) -> str:
        idx = self._used.get(debater.stance, 0)
        script = REBUTTAL_SCRIPT[debater.stance]
        line = script[idx % len(script)]
        self._used[debater.stance] = idx + 1
        return line


def build_llm() -> ChatOpenAI:
    """构建 DeepSeek 兼容客户端,低温保证裁决输出稳定。"""
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        temperature=0,
    )


JUDGE_PROMPT_TEMPLATE = (
    "你是校园 AI 社评审员社长,主持这场关于「{topic}」的正式辩论。\n"
    "以下是完整辩论记录:\n{transcript}\n"
    "请只回复三行,不要多余内容:\n"
    "胜方:<正方·产品负责人 / 反方·风险审查员>\n"
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
        prompt = JUDGE_PROMPT_TEMPLATE.format(
            topic=DEBATE_TOPIC, transcript="\n".join(transcript),
        )
        if MOCK:
            print("[MOCK] 评审员使用剧本裁决")
            raw = mock_verdict_text()
        else:
            raw = self.llm.invoke(prompt).content
        result: dict[str, object] = {}
        for line in str(raw).splitlines():
            if line.startswith("胜方:"):
                result["winner"] = line.split(":", 1)[1].strip()
            elif line.startswith("理由:"):
                result["reason"] = line.split(":", 1)[1].strip()
            elif line.startswith("置信度:"):
                result["confidence"] = float(line.split(":", 1)[1].strip())
        return result


def main() -> None:
    debaters = [Debater("产品负责人", "正方", "支持"), Debater("风险审查员", "反方", "反对")]
    records = Debate(debaters).run(rounds=2)
    verdict = Judge().verdict(records)
    print("[社长裁决]")
    for key, value in verdict.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
