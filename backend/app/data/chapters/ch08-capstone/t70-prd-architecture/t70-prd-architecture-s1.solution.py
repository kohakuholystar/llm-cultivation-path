"""终期交付 · s1:PRD 骨架——项目定位与用户故事

毕业设计的第一块砖:用「项目定位 + 目标 + 用户故事」搭出 PRD 开篇,
让需求从一句口号变成可评审、可验收的条目。
"""
import os


# ---- 项目定位:一份 PRD 的开头三件套 ----
PROJECT = {
    "name": "黑糖资料室",
    "tagline": "毕业设计 · 整合七章所学交付完整知识问答 Agent",
    "background": "技术社区资料浩如烟海,自学者常因无人指点而状态失控。本项目打造一名问答 Agent:学习者提问,它检索项目组资料、必要时调用工具,并给出带出处的回答。",
}

# ---- 项目目标:可量化,才能验收 ----
GOALS = [
    "能对学习问题给出带出处的答案,答非所问率低于 5%",
    "从提问到出答案的平均耗时不超过 3 秒",
    "支持至少 50 篇资料入库,检索命中率不低于 80%",
]

# ---- 极简 Markdown 渲染器:PRD 全部由数据 + 渲染生成 ----
def md_h2(text: str) -> str:
    """渲染二级标题。"""
    return f"\n## {text}\n"


def md_h3(text: str) -> str:
    """渲染三级标题。"""
    return f"\n### {text}\n"


def md_table(headers: list, rows: list) -> str:
    """把二维数组渲染成 Markdown 表格。"""
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def target_users() -> list:
    """返回目标用户表:[用户, 身份, 核心诉求]。"""
    return [
        ["入门自学者", "刚踏入技术社区的新人", "快速搞懂基础方法,少走弯路"],
        ["进阶用户", "卡在瓶颈多年的学习者", "按自身状态定制突破方案"],
        ["项目组执事", "管理知识库的负责人", "低门槛维护知识库内容"],
    ]


def user_stories() -> list:
    """返回用户故事表:[编号, 故事]。"""
    return [
        ["US-1", "作为入门自学者,我想要检索基础方法,以便三天内入门"],
        ["US-2", "作为进阶用户,我想要对比各资料的突破方法,以便选出最适合的"],
        ["US-3", "作为项目组执事,我想要批量导入资料,以便让知识库跟上黑糖资料室"],
    ]


def build_prd_part1() -> str:
    """渲染 PRD 第一章:项目定位 + 目标用户与用户故事。"""
    doc = ["# 黑糖资料室 PRD", "", "> 需求分析与系统设计文档(第一期)"]
    doc.append(md_h2("一、项目定位"))
    doc.append(f"- 项目名称:{PROJECT['name']}")
    doc.append(f"- 一句话定位:{PROJECT['tagline']}")
    doc.append(md_h3("背景"))
    doc.append(PROJECT["background"])
    doc.append(md_h3("目标"))
    for i, goal in enumerate(GOALS, 1):
        doc.append(f"{i}. {goal}")
    doc.append(md_h2("二、目标用户与用户故事"))
    doc.append(md_h3("目标用户"))
    doc.append(md_table(["用户", "身份", "核心诉求"], target_users()))
    doc.append(md_h3("用户故事"))
    doc.append(md_table(["编号", "故事"], user_stories()))
    return "\n".join(doc) + "\n"


def main() -> None:
    os.makedirs("docs", exist_ok=True)
    text = build_prd_part1()
    with open("docs/prd_part1.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(f"黑糖资料室 PRD 骨架已写入 docs/prd_part1.md,正文共 {len(text)} 字符")


if __name__ == "__main__":
    main()
