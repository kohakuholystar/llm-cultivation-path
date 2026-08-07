"""天庭辩论 · s4:最终立场与共识收敛

裁判已经给出裁决,但辩论是否真正「收敛」,还要看双方听完对方
全部发言后的态度。本步让每位辩论员用大模型重新表态最终立场,
再比较两人立场是否一致:一致即共识收敛,不一致则判定未收敛。
"""
import os
import sys

from langchain_openai import ChatOpenAI

DEBATE_TOPIC = "天庭的灵讯服务该由 Agent 全自动上线,还是保留人工复核?"

MOCK = os.environ.get("MOCK_LLM") == "1"
if not MOCK and not os.environ.get("OPENAI_API_KEY"):
    print("未检测到 API Key:请先在右上角 AI 配置填入 DeepSeek API Key。")
    print("(本地离线演示可设 MOCK_LLM=1,用剧本模拟最终表态)")
    sys.exit(0)

# 每个立场对应一句开篇立论
OPENING_SCRIPT = {
    "支持": "灵讯服务流程已全面自动化,Agent 上线又快又稳,人工复核纯属拖后腿。",
    "反对": "灵讯服务关系天庭民生,一旦 Agent 决策失误影响面巨大,必须保留人工复核。",
}

# 反驳词库:每个立场两句,按轮次循环取用
REBUTTAL_SCRIPT = {
    "支持": ["自动化能把错误率压到接近零,人工复核反而引入主观偏差。",
             "先全自动上线再灰度观测,比事事等人拍板更快暴露问题。"],
    "反对": ["灵讯一旦误判,影响的是成千上万仙民,快不等于对。",
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
    """构建 DeepSeek 兼容客户端,低温保证输出稳定。"""
    return ChatOpenAI(
        model=os.environ.get("MODEL_NAME", "deepseek-v4-pro"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com"),
        temperature=0,
    )


FINAL_STANCE_PROMPT_TEMPLATE = (
    "你是天庭辩手「{role}·{name}」,立场「{stance}」。"
    "听完对方全部发言后,请只回复一个词给出你的最终立场:支持或反对。\n"
    "完整辩论记录:\n{transcript}"
)


def mock_final_stance(name: str, stance: str) -> str:
    """剧本模式:司命星君被说服改口,其余按原立场表态。"""
    return "反对" if name == "司命星君" else stance


class Consensus:
    """共识检测器:收集最终立场,判断双方是否收敛。"""

    def __init__(self) -> None:
        self.llm = None if MOCK else build_llm()

    def ask_final_stance(self, debater: Debater, transcript: list[str]) -> str:
        if MOCK:
            print(f"[MOCK] {debater.name} 使用剧本表态")
            raw = mock_final_stance(debater.name, debater.stance)
        else:
            prompt = FINAL_STANCE_PROMPT_TEMPLATE.format(
                role=debater.role, name=debater.name,
                stance=debater.stance, transcript="\n".join(transcript),
            )
            raw = self.llm.invoke(prompt).content
        return "支持" if "支持" in str(raw) else "反对"

    def check_convergence(self, final: dict[str, str]) -> tuple[bool, str]:
        stance = next(iter(final.values()))
        if all(s == stance for s in final.values()):
            return True, f"双方达成共识,均持「{stance}」立场"
        return False, "双方仍各执己见,未收敛"


def main() -> None:
    debaters = [Debater("司命星君", "正方", "支持"), Debater("纠察灵官", "反方", "反对")]
    records = Debate(debaters).run(rounds=2)
    consensus = Consensus()
    final = {d.name: consensus.ask_final_stance(d, records) for d in debaters}
    print("[最终立场]")
    for name, stance in final.items():
        print(f"  {name}:{stance}")
    converged, note = consensus.check_convergence(final)
    print(f"[收敛判定] {'已收敛' if converged else '未收敛'} —— {note}")


if __name__ == "__main__":
    main()
